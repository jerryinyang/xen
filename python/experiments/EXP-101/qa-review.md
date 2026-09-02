## QA run 1 — 2026-08-11T03:52:39Z — mode: subagent — HEAD d9730b5982c8d4b4e2ed76f2f458d87e2ee70a03

Verdict: REVISE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Liquidity-level catalogue includes previous 1D/1W/4H/1H levels | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:6,56`; checkpoint `design.md:104` | DEVIATES | Checkpoint excludes 1W. |
| Sweep causal ordering and raid state | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:10-22`; checkpoint `design.md:131-153` | MATCHES | Strict excursion, inclusive return, ambiguity, ordering, and positive reversal are stated. |
| Value-gap interval and profile definition | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:43-49,67`; checkpoint `design.md:158-181` | MATCHES | Includes the strict rule `gap_span < 0.30*(VAH-VAL)`. |
| Timeframes, confirmation references, sessions, ATR, 1m input, fences and holdout | checkpoint `design.md:75-121,141-153,305-307` | MATCHES | 1H references are used for 15m/30m and 1D for 1h. |
| Controls and required emissions | checkpoint `design.md:204-253`; EXP-101 `design.md:46-55` | MATCHES | Design-only review; no implementation exists. |

### Golden-trace diff

No implementation or smoke emission exists. The design-only golden trace is consistent for the matched clauses; the 1W catalogue branch is an explicit deviation.

### Governance & boundary

- Review mode: fresh `subagent` context.
- No experiment was run and no implementation was reviewed.
- Reviewed state: 5 modified files and 11 untracked paths at the reviewer timestamp.
- Literal 100% SoT preservation is not established.

### Issues

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 2 — 2026-08-13T18:20:21Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75

Verdict: REVISE

Scope: EXP-101 only. Design/readiness review of the frozen EXP-100 AMENDMENT-13 TRAIN
emission; no Nautilus launch, TEST/holdout read, future-data inspection, or EXP-101
implementation review.

Reviewed git state before this append: HEAD
`3eb18d8683e7b5555331c88870db05d6334eea75`. Dirty files:

```text
M docs/experiments-docs/INDEX.md
M docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/design.md
M docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md
M docs/experiments-docs/families/cf-liqswp-001.md
M docs/signal-registry/README.md
M docs/signal-registry/candidate-families/cf-liqswp-001-universe.json
M docs/signal-registry/candidate-families/cf-liqswp-001.md
M docs/signal-registry/multiplicity-registry.md
M docs/superpowers/plans/2026-08-12-exp-100-progress-handoff.md
M docs/superpowers/specs/2026-08-11-liquidity-sweeps-design.md
M python/experiments/EXP-100/code/run_experiment.py
M python/experiments/EXP-100/code/run_matrix.py
M python/experiments/EXP-100/design.md
M python/experiments/EXP-100/qa-review.md
D python/experiments/EXP-100/results/estimand_validation_smoke.json
D python/experiments/EXP-100/results/execution/preflight-journal.jsonl
M python/experiments/EXP-101/design.md
M python/experiments/EXP-102/design.md
M python/experiments/EXP-102/qa-review.md
M python/experiments/EXP-103/design.md
M python/experiments/EXP-103/qa-review.md
M python/experiments/EXP-104/design.md
M python/experiments/EXP-104/qa-review.md
M python/experiments/INDEX.md
M python/src/xen/exp100/config.py
M python/src/xen/exp100/levels.py
M python/src/xen/exp100/processor.py
M python/src/xen/exp100/state_store.py
M python/src/xen/exp100/tpo.py
M python/tests/test_exp100_control.py
M python/tests/test_exp100_levels.py
M python/tests/test_exp100_matrix_runner.py
M python/tests/test_exp100_processor.py
M python/tests/test_exp100_state_store.py
M python/tests/test_exp100_tpo.py
?? .pi/
?? docs/superpowers/plans/2026-08-13-exp-100-amendment-10-12-rerun.md
?? docs/superpowers/plans/2026-08-13-exp-100-amendment-13-analysis-handoff.md
?? docs/superpowers/plans/2026-08-13-exp-100-amendment-13-rerun.md
?? docs/superpowers/plans/2026-08-13-exp-100-progress-handoff.md
?? docs/superpowers/specs/2026-08-12-exp-100-late-window-active-raid-optimization-design.md
?? python/experiments/EXP-100/analysis.md
?? python/experiments/EXP-100/analysis_code/
?? python/experiments/EXP-100/report.md
?? python/experiments/EXP-100/results/analysis/
?? python/experiments/EXP-100/results/estimand_validation.json
?? python/experiments/EXP-100/results/execution/full-journal.jsonl
?? python/experiments/EXP-100/results/execution/full/
```

EXP-101 has no `code/`, runner, analysis package, or smoke emission. The frozen EXP-100
path is therefore the only implementation/readiness evidence. It is sufficiently specified
for causal raw level/raid/outcome extraction and validity gating, but not yet sufficiently
specified for EXP-101's level-significance analysis.

### Design-fidelity trace

| Design clause (§ref) | Code/emission evidence | Verdict | Notes |
|---|---|---|---|
| Family, cTrader universe, TRAIN fence, 15m/30m/1h grid, 1H/4H confirmation, 264 cells (§1, §3) | `python/experiments/EXP-101/design.md:3-15,43-50`; checkpoint `design.md:147-173,208-228`; family `cf-liqswp-001.md:20-44`; EXP-100 `config.py:16-32,76-100`, `run_matrix.py:104-148` | MATCHES | Current scope retains 1W; the prior QA run's withdrawn-1W issue is resolved. |
| Family A/B/C level catalogue and stable coincident-level identity (§3) | Checkpoint `design.md:160-173`; family `cf-liqswp-001.md:34-47`; EXP-100 `levels.py:21-41,121-173`; `strategy.py:164-178` | MATCHES | Current configurations are `PREVIOUS_1H/4H/1D/1W`, sessions, and `ROLLING_7/14/22/252`; no `C-16` configuration exists. |
| Observation-bar raid start, inclusive return, AMENDMENT-13 lifetime (§1, §4) | Checkpoint `design.md:187-206`; EXP-100 `processor.py:256-295,321-391`; analysis `analysis.md:150-156` | MATCHES | Same-bar pierce/return remains live; 1m-only wicks do not create raids. |
| Close-all-eligible settlement and primary/non-primary/failure states (§1, §4) | Checkpoint `design.md:201-228`; EXP-100 `processor.py:432-503,519-590`; analysis `analysis.md:158-161` | MATCHES | The frozen emission contains `COMPLETED`, `CONFIRMED_NON_PRIMARY`, and `FAILED_BREAKOUT` rows. |
| Confirmation methods/references and separate configuration strata (§3) | Checkpoint `design.md:208-228`; EXP-100 `processor.py:628-652`; `config.py:76-85` | MATCHES | No EXP-101 code exists; the frozen EXP-100 cells use the registered grid. |
| Primary outcomes `swing_atr`, `swing_duration`, `strong_move` (§3) | EXP-101 `design.md:52-54`; EXP-100 schema `strategy.py:183-215`; computation `processor.py:519-579` | DEVIATES / MISSING | `swing_atr` and `strong_move` are emitted, but the source field is `duration_ns`, not `swing_duration`; the design gives no units/field mapping, no inclusion rule for primary vs non-primary/failed/censored rows, and no missing-outcome rule. |
| Future-destroy control must test the level/outcome contrast (§4) | EXP-101 `design.md:59-75`; EXP-100 `run_experiment.py:476-507`; `control.py:61-187` | DEVIATES | The frozen destroy deranges outcome values only within `archive_symbol × timeframe × config`. It preserves each configuration's outcome distribution, so a between-configuration level-significance contrast can survive unchanged. This is a valid EXP-100 apparatus check, not a sufficient EXP-101 tripwire. |
| Clustered uncertainty and fixed comparator (§4, §5) | EXP-101 `design.md:78-91`; checkpoint `design.md:333-355` | MISSING | `level_id` clustering is named, but the estimator/interval/bootstrap method, exact comparison population, and fixed baseline for ordered/pairwise family contrasts are not predeclared. “All raids in the same family/configuration stratum” is not an unambiguous common comparator. |
| Operator-only bands and sample-size handling (§5) | EXP-101 `design.md:81-91`; checkpoint `design.md:333-355` | PARTIAL | No rows are hidden and no machine value verdict is declared, but channel declarations are shorthand rather than explicit `sigma_denominator` fields and the analysis population remains undefined. |
| Golden trace (§6) | EXP-101 `design.md:94-101`; current config set `config.py:19-32`; synthetic EXP-100 evidence `analysis.md:195-203` | DEVIATES / MISSING | The trace names retired `C-16`, gives no timestamps/input state/expected outcome values, and does not provide a hand-checkable current 1H-versus-7/14/22/252 event. |
| Hard/informative split and zero-cost boundary (§7) | EXP-101 `design.md:103-125`; pipeline config `_pipeline-config.md:181-215`; EXP-100 analysis `analysis.md:35-49` | MATCHES | The canonical zero-cost disclosure is present; no cost directive or value/deployability claim is introduced. |

### Golden-trace diff

No EXP-101 implementation or smoke emission exists, so no implementation-level EXP-101
golden diff is possible.

| Design event | Frozen EXP-100 evidence | Verdict |
|---|---|---|
| Coincident levels remain separate | `level_id`, `event_identity`, and `source_configuration` are distinct fields in `strategy.py:164-178`; the EXP-100 synthetic trace records separate T1/T2 rows (`analysis.md:158-161,195-203`) | MATCHES for raw object identity. |
| “A 1H level and a C-16 level” receive separate rows | Current frozen configuration set contains `PREVIOUS_1H` and `ROLLING_7/14/22/252`, not C-16 (`config.py:19-32`) | DEVIATES. |
| Separate significance labels and outcome rows | EXP-100 emits raw level/raid/outcome rows; no EXP-101 analysis code or label artifact exists | MISSING. Labels must remain operator-only and the design must state the exact analysis output. |
| Later confirmed swing expected from the trace | EXP-100 has `swing_atr`, `duration_ns`, and `strong_move`, but the trace supplies no hand-derived timestamp, status, price, duration, or ATR expectation | MISSING. |

### Governance & boundary

- **Fresh-context requirement:** PASS — this run is recorded as `mode: subagent`; no EXP-101 implementation work exists in this context.
- **Frozen emission/readiness:** PARTIAL — EXP-100 has 264 published cTrader TRAIN cells, per-cell/family validity artifacts, and the required raw outcome fields; EXP-100 analysis reports `blocking_pass` for 264/264 cells and a non-vacuous zero-fixed-point destroy (`analysis.md:30-49,125-131`).
- **Fence and holdout:** PASS for the reviewed path — the cTrader INFR-021 TRAIN fence and no-TEST/no-holdout boundary are documented and the EXP-100 analysis reports zero holdout timestamps (`analysis.md:41-46,205-209`). No TEST/holdout/future data was loaded or inspected in this review.
- **Family/registry precondition:** PASS — `CF-LIQSWP-001` is registered, EXP-101 is the registered HYP-001 route, and the registry records zero counted TEST reads with holdout sealed (`cf-liqswp-001.md:3-8,109-148`; `multiplicity-registry.md:1710-1724`).
- **Causality and one-node boundary:** PASS for frozen EXP-100 — the processor implements observation-bar chronology and the runner enforces one `BacktestNode` per process (`run_experiment.py:409-425`; `run_matrix.py:417-418`).
- **Python backtest/local accounting:** PASS for this review — EXP-101 has no implementation; the frozen EXP-100 artifact is a no-order measurement emission, and its analysis records no local accounting definitions (`analysis.md:42-47`).
- **Zero-cost / powering / PSR:** PASS / N/A — canonical zero-cost text is present; no research MDE/power machinery is present; no mean trade/leg bps series is defined, so PSR pairing is not activated.
- **Derangement:** PASS for the existing EXP-100 control only — `control.py:100-150,180-187` creates a zero-fixed-point cyclic mapping. It does not pass the EXP-101 contrast-specific bite because it preserves configuration marginals.
- **Screen conversion, XENA, and battery eligibility:** screen conversion and XENA checks are N/A; the multi-cell design does not declare the §13 battery/eligibility/null applicability or an exit-matched null treatment required by the shared rules.

### Issues

1. **REVISE — failing artifact: `python/experiments/EXP-101/design.md`; required skill: `quant-designer`.** Replace or supplement the within-configuration destroy with a predeclared derangement/null that can actually collapse the HYP-001 between-level/configuration contrast, while stating preserved populations/marginals and the blocking bite.
2. **REVISE — failing artifact: `python/experiments/EXP-101/design.md`; required skill: `quant-designer`.** Replace retired `C-16` and expand the golden trace to current configurations with timestamps, input state, expected status/price/outcome values, and hand-derived ATR/duration expectations.
3. **REVISE — failing artifact: `python/experiments/EXP-101/design.md`; required skill: `quant-designer`.** Pin the analysis population and censoring/status rules, map `swing_duration` to `duration_ns` with units, and define the fixed comparator, contrast estimators, clustering/bootstrap uncertainty, and output rows before reading the frozen emission.
4. **REVISE — failing artifact: `python/experiments/EXP-101/design.md`; required skill: `quant-designer`.** Add the shared multi-cell battery/eligibility/null applicability statement, explicit per-channel `sigma_denominator` declarations, and the amendment-ledger/final-null accounting required by the governance rules.

## QA run 3 — 2026-08-14T16:51:58Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: fresh-context, analysis-only review of the current EXP-101 design against the retained
EXP-100 AMENDMENT-14 TRAIN emission. No EXP-100 modification, execution, rerun, or re-emission;
no EXP-101 implementation; no TEST or holdout access.

Reviewed git state before this append:

```text
 M python/experiments/EXP-101/design.md
 M python/experiments/EXP-102/design.md
```

### Prior-issue verification

| QA-run-2 issue | Current verdict | Evidence |
|---|---|---|
| Contrast-specific future destroy | PARTIAL | The new cross-configuration perfect-matching derangement can move configuration contrasts (`design.md:112-140`), but the hard tripwire still lacks an exact acceptance/failure equation (`design.md:142-148`). |
| Current-config golden trace | RESOLVED | Retired `C-16` is gone; PREVIOUS_1H and ROLLING_7 have timestamps and hand-derived outcomes (`design.md:182-195`). |
| Population, censoring, field map, comparator, estimator | PARTIAL | Population/censor/comparators/bootstrap parameters are now stated (`design.md:79-107`), but the duration source map is factually wrong and the strong-move estimator is internally inconsistent. |
| Multi-cell rules, channel denominators, amendment/final-null ledger | RESOLVED | Explicit channels and thin-row policy (`design.md:164-177`); 2L/3T/8N ledger and §13 applicability (`design.md:208-245`). |

### Design-fidelity trace

| Design clause (§ref) | Code/emission evidence | Verdict | Notes |
|---|---|---|---|
| Frozen AMENDMENT-14 source, 264-cell gate precondition (§ Frozen source) | `design.md:12-34`; `EXP-100/results/estimand_validation.json`; 264 `results/execution/full/*.json` | MATCHES | Family gate is `blocking_pass=true`, `n_cells=264`; all 264 per-cell gates are true. Gate was checked before source-row inspection. |
| Source seal and current checkpoint (§ Frozen source) | checkpoint `design.md:89-119,154-180`; 264 `run_metadata.json` and `fence_attestation.json` | MATCHES | 264 unique config hashes; all event-log hashes verified; contract `nautilus-emission-v1`, Nautilus `1.230.0`, `NO_COST_CHARGED`, one node, and pinned manifest hash match. |
| AMENDMENT-14 boundary (§ Frozen source) | `design.md:37-42`; checkpoint `design.md:110-119`; raid schema `strategy.py:221-232` | MATCHES | `pre_mfe_retrace` is present and explicitly outside HYP-001. |
| Binding ATR_UNDEFINED exclusion (§ Frozen source; § Scope) | `design.md:22-26,85-97,201-204`; EXP-100 `report.md:58-85,114-122` | MATCHES | All rows remain visible for counts; ATR-undefined excursion/normalised-excursion/strong-move derivatives are excluded without repair or substitution. This matches the operator verdict. |
| Exact duration field map (§ Frozen source) | `design.md:37-42`; `strategy.py:230-232`; `processor.py:587-612`; retained `raids.parquet` schema | DEVIATES | The design says `swing_duration_ns` is not emitted. It is emitted beside `duration_ns`; all 9,840,478 retained rows have identical values and nullness in the two columns. |
| Mechanism/object identity (§ Mechanism; § Object identity) | `design.md:47-67`; checkpoint `design.md:123-151` | MATCHES | Same level-attributed raid/outcome object; no orders/fills; repeated-level dependence is clustered. |
| Configuration strata and fixed controls (§ Scope) | `design.md:72-83`; checkpoint `design.md:171-184,274-288`; family registry `cf-liqswp-001.md:116-123` | MATCHES | Current 4/3/4 configuration catalogue and Family A/B/C fixed baselines are explicit; pooled reads are disclosure-only. |
| Population, statuses, censoring, ATR boundary (§ Scope) | `design.md:85-97`; `processor.py:540-615`; raid schema `strategy.py:171-233` | MATCHES | Primary population is exact; failed/non-primary/censored/null/thin rows remain disclosed. |
| Continuous estimator and uncertainty (§ Scope) | `design.md:99-107` | PARTIAL | Outcomes, percentile level, seeds, resamples, block lengths, level-cluster unit, and sensitivity are pinned. Contrast sign and whether comparator/arm cluster blocks are resampled independently or jointly are not explicit. |
| Strong-move estimator (§ Mechanism; § Scope; § Sample-size) | `design.md:53-54,105-106,169-172` | DEVIATES | The operative sentence correctly says two **unpaired** cluster-bootstrap proportions, but mechanism and channel declarations still call the labels/contrast **paired** and use `paired_delta`. |
| Crosswise control mapping (§ Control) | `design.md:112-140` | MATCHES | The lexicographically first perfect cross-config matching is deterministic, moves each outcome block once, forbids same raid/config, and preserves event labels/counts. A gated TRAIN count-only check found 155/174 grouping classes feasible; the declared VOID path covers the 19 infeasible classes (42 rows). |
| Hard tripwire decision (§ Tripwire) | `design.md:130-148`; design requirements §4 | MISSING | Synthetic plant, derangement, disclosures, and `INTEGRITY_Z=2.8` are present, but “must remove/collapse” is not converted into an exact statistic and pass/fail inequality. `outcome-nullness class` is also not defined as a specific field-null bitmap. |
| Golden trace (§ Golden trace) | `design.md:182-195`; `processor.py:300-328,400-428,462-522,540-612` | MATCHES | Independent config cells remain separate; raid start/return/primary completion and the 2.00 price / 2.00 ATR / 200 bps / 1h duration / strong=true arithmetic match source logic. |
| Hard/informative split, amendment direction, final null (§ Governance) | `design.md:201-245`; design requirements §§8,12-13 | MATCHES | Integrity alone blocks; no machine qualifier or count hide rule; final 2L/3T/8N accounting is correct and no directional streak reaches three. |
| Canonical zero-cost text (§ Zero-cost) | `design.md:251-261`; pipeline config canonical disclosure | MATCHES | Canonical text appears verbatim. No cost directive, cost call, or prohibited claim is in EXP-101. |

### Golden-trace diff

| Event | Expected from design | Source logic | Verdict |
|---|---|---|---|
| T1 — separate PREVIOUS_1H/ROLLING_7 cells | Each 100.00 high starts its own raid; initial 101.20 high gives excursion 1.20, count 0, no return | `_new_raid` keys identity by the cell level and computes side-aware excursion (`processor.py:400-458`); source configuration is emitted (`strategy.py:174-180`) | MATCHES |
| T2 — later return and expected-side confirmation | 100.00 touch records return; 11:00 expected-side close leaves one primary raid per independent cell | Return is inclusive (`processor.py:300-328`); expected event chooses the latest only among raids in that process/cell (`processor.py:467-518`) | MATCHES |
| T3 — opposing endpoint | 98.00 favorable extreme from level 100 gives 2.00 price, 2.00 ATR, 200 bps, 3.6e12 ns, and `2.00 > 1.20` | Endpoint logic computes exactly those side-aware fields and duration (`processor.py:540-612`) | MATCHES |

No EXP-101 analysis implementation or smoke output exists, so this is a hand-diff against the
frozen source schema/logic rather than an implementation-output comparison.

### Governance & boundary

- **Fresh context:** PASS — mode is `subagent`; this context did not create EXP-100 or the EXP-101 design.
- **Checkpoint/registry:** PASS — checkpoint 019 includes AMENDMENT-14 and the 264-cell cTrader scope; `CF-LIQSWP-001/HYP-001` is registered with 0 candidate slots and 0 counted TEST reads.
- **TRAIN/holdout:** PASS — only the declared TRAIN emission and metadata were inspected after the family gate check. No TEST or global-holdout path was opened.
- **Read-only source:** PASS — EXP-100 was not changed or run. EXP-101 has no `code/`; `analysis_code/` is empty.
- **Local accounting/Python backtest:** PASS — `check_no_local_accounting` returns `ok=true` for both prospective EXP-101 code paths; no strategy backtest exists.
- **One-node/cost:** PASS — all 264 metadata files state `one_backtest_node=true` and `NO_COST_CHARGED`; all event hashes and pinned fence hashes verify.
- **Powering/PSR:** PASS/N/A — no research MDE, floor, power curve, count veto, or machine `UNPOWERED`; no trade/leg-bps mean exists, so PSR pairing is N/A.
- **Screen conversion/XENA/cost directive:** N/A — no screen-money conversion, XENA route, or requested cost model.
- **Battery rules:** PASS/N/A as declared — no battery selection, capped read, exit selection, or phase-shift gate; all counts remain visible.

### Issues

1. **REVISE — exact estimator is internally inconsistent.** `design.md:53-54,105-106,169-172` calls `strong_move` both paired and unpaired. Make it unpaired everywhere, use an unpaired-proportion denominator declaration, state the contrast orientation (arm minus fixed baseline), and state whether arm/baseline cluster blocks are resampled independently or jointly. **Failing artifact:** `design.md`. **Required skill:** `quant-designer`.
2. **REVISE — frozen duration schema is misstated.** `design.md:37-42` says `swing_duration_ns` is not emitted, but `strategy.py:230-232`, `processor.py:610-612`, and every retained parquet schema emit both `swing_duration_ns` and alias `duration_ns`. Name the canonical source column accurately and treat the other as the byte-equal emitted alias. **Failing artifact:** `design.md`. **Required skill:** `quant-designer`.
3. **REVISE — the hard tripwire has no executable decision rule.** `design.md:130-148` specifies the destroy but not the exact planted-contrast statistic/SE inequality that means collapse versus integrity failure; it also leaves `outcome-nullness class` undefined. Define the per-field nullness class and a deterministic `INTEGRITY_Z × bootstrap_SE` pass/fail equation using the same estimator, without turning it into a research/value floor. **Failing artifact:** `design.md`. **Required skill:** `quant-designer`.

## QA run 4 — 2026-08-14T17:09:53Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: shared fresh-context readiness review of the current full EXP-101 design against prior
QA, checkpoint 019 through AMENDMENT-14, and the completed read-only EXP-100 TRAIN source.
The EXP-100 family gate was read before source evidence. No EXP-100 command, modification,
rerun, or re-emission occurred; no analysis implementation was created; no TEST or holdout
artifact was accessed.

Reviewed dirty state before all four appends:

```text
 M python/experiments/EXP-101/design.md
 M python/experiments/EXP-101/qa-review.md
 M python/experiments/EXP-102/design.md
 M python/experiments/EXP-102/qa-review.md
 M python/experiments/EXP-103/design.md
 M python/experiments/EXP-104/design.md
```

### Design-fidelity trace

| Design clause (§ref) | Frozen source / governing evidence | Verdict | Notes |
|---|---|---|---|
| Read-only 264-cell AMENDMENT-14 source and gate-first rule (§ Frozen source) | `design.md:12-34`; `EXP-100/results/estimand_validation.json`; checkpoint `status.md:7-24` | MATCHES | Family gate says `blocking_pass=true`, `n_cells=264`; completed source remains read-only and TRAIN-only. |
| Field aliases and AMENDMENT-14 boundary (§ Frozen source) | `design.md:37-43`; `strategy.py:171-232`; `processor.py:580-612` | MATCHES | `config`/`source_configuration`, IDs, outcome fields, canonical `swing_duration_ns`, byte-equal `duration_ns`, and excluded `pre_mfe_retrace` scope are exact. |
| Configuration populations, fixed baselines, statuses, censoring (§ Scope) | `design.md:69-99`; checkpoint `design.md:274-288`; EXP-100 report `:38-85` | MATCHES | Family A/B/C baselines and primary-completed population are fixed; failed/non-primary/censored/thin rows remain visible. |
| Binding ATR_UNDEFINED exclusion (§ Frozen source; § Scope) | `design.md:22-26,94-98`; checkpoint `status.md:9-21`; EXP-100 report `:58-85` | MATCHES | Counts/status remain; excursion, normalized-excursion, `strong_move`, and derived interpretation are excluded without reconstruction or substitution. |
| Primary estimators and clustered uncertainty (§ Scope) | `design.md:100-115` | MATCHES (design-level) | Contrast sign, independent arm/baseline cluster blocks, circular draw/truncation, seeds, quantiles, sensitivity, empty-arm output, and unpaired strong-move proportions are pinned. No EXP-101 implementation exists. |
| Cross-configuration derangement (§ Control) | `design.md:119-149`; requirements §§3-4; L-28 | MATCHES for mapping | Rejection sampling is a uniform zero-fixed-point derangement; exact nullness bitmap, grouping, moved block, seed battery, and singleton VOID path are stated. |
| Future-destroy hard decision and fixture (§ Tripwire) | `design.md:151-164`; governance N6b; requirements §4 | MISSING / DEVIATES | The only executable inequality is on a synthetic plant. There is no hard same-estimator rule for a real observed contrast that survives destruction. The claimed duration and binary `strong_move` bite also have no numeric plants, and `bootstrap_SE_mean_destroyed`/collapse fraction are not operationally defined. |
| Golden trace (§ Golden trace) | `design.md:198-211`; `processor.py:285-350,470-612` | MATCHES | Separate cells, inclusive return, primary completion, 2.00 price/ATR, 200 bps, 3.6e12 ns, and `2.00 > 1.20` are hand-derivable and agree with frozen logic. |
| Amendment ledger/final null and canonical zero cost (§ Governance; § Zero cost) | `design.md:214-262,267-277`; checkpoint amendments 2-14; shared config canonical block | MATCHES | Complete 2L/3T/8N ledger, zero machine false qualifiers, no selection gate, and verbatim canonical disclosure. |

### Golden-trace diff

| Event | Design expectation | Frozen logic | Verdict |
|---|---|---|---|
| T1 | PREVIOUS_1H and ROLLING_7 cells independently start 1.20 excursions with count 0 | Cell-local level/raid identity and side-aware excursion are emitted | MATCHES |
| T2 | Inclusive 100.00 return; expected-side 1H event assigns one primary in each independent cell | Observation return and cell-local close-all logic preserve separate configurations | MATCHES |
| T3 | Opposing event emits swing 2.00 / 2 ATR / 200 bps / 1 hour / strong true | Terminal arithmetic and duration alias implement those exact values | MATCHES |
| Plant/control | Every declared outcome channel is destroyed and the live affected result cannot survive | Only the +0.50 ATR plant and fixture-only inequality are defined | MISSING |

### Governance & boundary

- Fresh-context subagent: PASS. Prior QA issues on duration alias, paired/unpaired wording,
  estimator orientation, and mapping were resolved.
- Registry/fence/read accounting: PASS. HYP-001 is registered with 0 candidate slots and 0
  counted TEST reads; no TEST/holdout access occurred.
- Read-only/no implementation: PASS. EXP-100 was not run or changed; EXP-101 `analysis_code/`
  is empty and no Python backtest or local accounting path exists.
- One-node, cost, powering, PSR: PASS/N/A. Frozen metadata attests one node and
  `NO_COST_CHARGED`; no live cost call, research power machinery, or trade/leg mean exists.
- Multi-cell rules: PASS/N/A as declared. No battery selection, exit selection, phase-shift
  retention gate, capped read, or row hiding exists.

### Issues

1. **REVISE — the hard future-destroy contract is incomplete.** `design.md:151-164` validates
   only a synthetic `swing_atr` fixture. Add the predeclared same-population/same-estimator
   hard rule for an observed raw contrast that survives destruction, exact definitions and
   computation order for `bootstrap_SE_mean_destroyed` and the disclosed control/raw fraction,
   and numeric fixtures for every outcome channel the control claims to referee (including
   duration and binary `strong_move`). Keep `INTEGRITY_Z=2.8` validity-only.
   `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.



## QA run 5 — 2026-08-14T17:30:00Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: **REVISE**

Reviewed git state uses the last recorded HEAD above. Git status was not re-queried because this review had read-only tools. Existing `qa-review.md` contains four prior runs; this run is supplied for append-only persistence.

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Frozen EXP-100 AMENDMENT-14 source and 264-cell gate (§1, lines 8–34) | `python/experiments/EXP-101/results/estimand_validation.json:1–19`; EXP-100 metadata | MATCHES | Gate reports `blocking_pass=true`, 264 cells, pinned TRAIN fence. |
| Level configurations and identity (§3, lines 72–83) | `python/src/xen/exp100/config.py:19–32`; `levels.py:21–41,121–173` | MATCHES | All 11 configurations and configuration-specific identities are present. |
| Causal raid, return, confirmation, and endpoint logic (§§2–3, lines 50–107) | `processor.py:285–328,400–458,462–612` | MATCHES | Inclusive return, live same-bar raid, primary attribution, opposing endpoint, and duration updates agree. |
| Field aliases and ATR exclusion (§1/§3, lines 37–45, 94–107) | `strategy.py:171–232`; `processor.py:580–612`; EXP-100 report §ATR exclusion | MATCHES | `swing_duration_ns` is canonical and `duration_ns` is emitted as its alias; ATR-undefined rows are excluded from ATR-derived outcomes. |
| EXP-101 estimators and neutral output (§4, lines 109–153) | `python/experiments/EXP-101/analysis_code/` is empty; no EXP-101 implementation exists | **MISSING** | No code implements cluster bootstrap, fixed-comparator contrasts, output rows, or neutral report layers. |
| Cross-configuration future destroy (§5, lines 159–242) | Existing EXP-100 control: `run_experiment.py:476–507`; `control.py:61–187` | **MISSING** | Existing control uses one seed, groups by `archive_symbol × timeframe × config`, and does not implement EXP-101’s 2,000 cross-configuration derangements, outer bootstrap, or live tripwire. |
| Golden trace (§7, lines 284–300) | `levels.py:110–147`; `processor.py:285–328,400–458,462–612` | MATCHES | Hand-derived T1–T3 behavior agrees with frozen source logic. No EXP-101 smoke output exists. |
| Hard/informative split and amendment accounting (§6/§8, lines 265–342) | Design text; registry `multiplicity-registry.md:1710–1725` | MATCHES | No value gate, row hiding, power machinery, or unapproved amendment is present. |
| Zero-cost disclosure (§9, lines 345–355) | Design and source metadata | MATCHES | Canonical disclosure is present; metadata reports `NO_COST_CHARGED`. |

### Golden-trace diff

| Event | Expected from design | Frozen source logic | Verdict |
|---|---|---|---|
| T1 | Independent PREVIOUS_1H and ROLLING_7 levels at 100.00 start separate raids with 1.20 excursion | Cell-local configuration and level identity are preserved; strict beyond test starts the raid | MATCHES |
| T2 | Inclusive 100.00 return; later expected-side close independently assigns primary attribution | `processor.py:285–328,462–522` records return and performs cell-local primary selection | MATCHES |
| T3 | First opposing event produces price 2.00, ATR 2.00, 200 bps, one-hour duration, `strong_move=true` | `processor.py:180–196,540–612` updates the favorable extreme and computes terminal outcomes | MATCHES |
| EXP-101 control | All declared channels must be tested by cross-configuration derangement | No EXP-101 control or smoke emission exists | **MISSING** |

### Governance & boundary

- **Fresh context:** PASS — this is a dedicated `subagent` review.
- **Gate-first:** PASS — EXP-101’s inherited 264-cell estimand gate reports `blocking_pass=true`; no false cell gate was found.
- **TRAIN/holdout:** PASS for retained source — EXP-100 analysis reports zero holdout rows and no post-TRAIN timestamps.
- **Registry:** PASS — `CF-LIQSWP-001/HYP-001` is registered with zero candidate slots and zero counted TEST reads.
- **No Python backtest:** PASS — EXP-101 has no executable strategy or runner.
- **Local accounting:** NOT RUN — `python/experiments/EXP-101/code/` does not exist; the required path check must be run after implementation is added.
- **One-node boundary:** PASS for retained EXP-100 metadata; no new node is requested by EXP-101.
- **Derangement:** PARTIAL — design requires valid derangements, but the only existing control is the incompatible EXP-100 within-configuration control.
- **Zero cost:** PASS — canonical disclosure and `NO_COST_CHARGED` metadata verified.
- **Power/MDE denylist:** PASS — no research power, MDE, detection-floor, or machine power labels.
- **PSR:** N/A — no trade or leg-bps series.
- **Screen conversion/XENA:** N/A.
- **Battery rules:** PASS as declared — no adaptive selection, capped read, or path-dependent exit gate; all realised rows must remain visible.

### Issues

1. **HIGH — EXP-101 implementation is absent.**
   **Design:** §1 lines 8–15 and §§4–6 lines 109–277.
   **Evidence:** `python/experiments/EXP-101/code/` and `python/experiments/EXP-101/analysis_code/` contain no files.
   **Why it matters:** The estimator, output contract, censoring handling, and hard integrity gate cannot be verified or executed.
   **Required owner/change:** `experiment-developer`/analysis owner must add the independent EXP-101 implementation under the declared analysis boundary and provide a smoke emission before execution approval.

2. **HIGH — The available EXP-100 control cannot satisfy EXP-101’s control contract.**
   **Design:** §5 lines 159–242.
   **Evidence:** `python/experiments/EXP-100/code/run_experiment.py:476–507`; `python/src/xen/exp100/control.py:61–187`.
   **Why it matters:** The existing control preserves each configuration’s marginal by grouping on `config`; it uses one seed and omits the required cross-configuration 2,000-seed control, outer bootstrap, duration canonical field, and live same-estimator tripwire. Reusing it could certify a confounded placebo rather than the EXP-101 contrast.
   **Required owner/change:** Implement the declared cross-configuration derangement and exact `INTEGRITY_Z × bootstrap_SE` rule in EXP-101 analysis code; do not reuse the EXP-100 control as validation.

### Summary

**REVISE.** The frozen source, design, golden trace, registry, fence, and zero-cost boundaries are consistent. Execution is not ready because EXP-101 has no implementation or smoke emission, and the existing EXP-100 control is not a valid substitute for the required cross-configuration tripwire.

## QA run 6 — 2026-08-14T23:22:36Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: **REVISE**

Scope: the operator-requested single exhaustive implementation review of EXP-101's new
`analysis_code/`. Requirements were derived from the design before code inspection. This
review did not run live analysis, open TEST/holdout data, execute Nautilus, or modify design,
implementation, source emissions, or registry state. It appended this review only.

Reviewed dirty state before append:

```text
 M python/experiments/EXP-101/design.md
 M python/experiments/EXP-101/qa-review.md
 M python/experiments/EXP-102/design.md
 M python/experiments/EXP-102/qa-review.md
 M python/experiments/EXP-103/design.md
 M python/experiments/EXP-103/qa-review.md
 M python/experiments/EXP-104/design.md
 M python/experiments/EXP-104/qa-review.md
 M python/experiments/INDEX.md
?? python/experiments/EXP-101/analysis_code/
?? python/experiments/EXP-101/results/fixture_integrity.json
?? python/experiments/EXP-102/analysis_code/
?? python/experiments/EXP-102/results/fixture_integrity.json
?? python/experiments/EXP-103/analysis_code/
?? python/experiments/EXP-103/results/fixture_integrity.json
?? python/experiments/EXP-104/analysis_code/
?? python/experiments/EXP-104/results/fixture_integrity.json
?? python/tests/test_exp10x_analysis_contract.py
```

### Prior-finding resolution audit

| Prior issue | Verdict | Evidence |
|---|---|---|
| EXP-101 implementation absent | RESOLVED | `analysis_code/analysis.py` now exists and the fixture artifact is present. |
| EXP-100 within-config control was not an EXP-101 substitute | RESOLVED IN INTENT; IMPLEMENTATION DEFECTS REMAIN | A new cross-config control exists at `analysis.py:305-359,820-869`, but its population and hard-stop behavior deviate below. |
| Exact unpaired estimator, duration alias, and tripwire equation | MATCHES IN CORE HELPERS | `analysis.py:123-177,180-288,695-722`; source alias check `:997-998`. |

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Gate before source rows; 264 passing cells; per-cell execution gates (§1) | `analysis.py:880-950` | PARTIAL | Family gate, cell count, cost, metadata and event hash are checked before parquet reads. The required `EXP-100/results/execution/full/<cell>.json` gates are never opened, and metadata `config_hash` is only format-checked rather than reconciled to the gate's `catalog_attestation.config_hash`. |
| Frozen schema/object aliases and cell identity (§1) | `analysis.py:958-1003` | DEVIATES | Duration equality is asserted, but required input omits `source_configuration`; `config == source_configuration`, cell metadata↔row config/symbol/timeframe/method/reference, duplicate object IDs, and row/profile count reconciliation are not checked. |
| TRAIN-only fence and causal provenance (§1, §6 HARD) | `analysis.py:939-947,992-1001` | PARTIAL | Upper timestamps and pinned fence metadata are checked. No row-level chronology proves `sweep_ts_ns <= confirmation_ts_ns <= endpoint_ts_ns`, or traces the outcome fields to their causal source timestamps. |
| Completed-primary population and ATR exclusion (§3) | `analysis.py:60-68,123-177,586-594` | MATCHES for estimator rows | Completed primary rows are selected; ATR-undefined rows are excluded only from `swing_atr`/`strong_move`. |
| Fixed family comparators and arm-minus-baseline means (§3–4) | `analysis.py:123-177,659-692` | MATCHES | Family A/B/C comparator mapping and contrast orientation match. Strong-move booleans are averaged as an unpaired proportion. |
| Every requested summary, status/censor composition and missingness per result row (§3–4) | `analysis.py:597-656` | DEVIATES | No raw `swing_price`/`swing_bps` summaries are produced. Status counts are pooled across all configs and repeated on every arm row; missingness/exclusions combine arm and comparator rather than naming each population. |
| Five-seed cluster bootstrap, L=5 plus L=2/10 sensitivity (§4) | `analysis.py:180-288,618-623` | DEVIATES | The L=5 mechanics match, but live analysis never calls L=2 or L=10. `LENGTHS=(2,5,10)` is metadata only. |
| Complete cross-config destroy grouping (§5) | `analysis.py:291-359` | DEVIATES | Design grouping is exact stratum + status + primary-completed + five-bit nullness. Code additionally partitions by `primary_attribution`, `profile_status`, and profile undefined reason, and uses a six-bit non-finite class. A focused two-row trace that should form one design group instead produced two singleton VOIDs and moved zero rows. |
| Same population/estimator for live destroy and bootstrap SE (§5; N6b) | `analysis.py:725-817,820-869` | **MISSING** | Live destroy uses all configurations in the stratum, while `joint=False` outer bootstrap drops every configuration except the current arm and comparator. The destroyed mean and its SE therefore use different populations, invalidating the hard inequality. |
| Missing derangement/statistic is invalid, and survival blocks affected result (§5) | `analysis.py:695-722,820-869` | **MISSING** | Singleton/VOID counts and changed-field non-vacuity never feed the attestation. `VOID_FUTURE_DESTROY_SURVIVAL` is merely nested output; there is no aggregate blocking result, exception, or suppression of the affected observation. Analysis can continue after the design's hard failure. |
| Destroy disclosures: all draws, mean, empirical 95% interval, collapse ratio, mapping diagnostics (§5) | `analysis.py:839-869` | PARTIAL | Draws, mean, ratio and mapping totals exist; the live empirical 95% destroyed interval and per-VOID population reasons/counts are absent. |
| Fixture topology and exact §4 mechanics (§5 fixture) | `analysis.py:362-524` | DEVIATES | Plants and exact effects match, but `_fixture_outer_integrity` uses independent iid row sampling (`rng.choice`) rather than the declared circular whole-cluster bootstrap. With one-row clusters, L=5 still changes adjacent cluster selection, so the fixture does not validate the live bootstrap implementation it claims to check. |
| Golden trace T1–T3 (§7) | Frozen EXP-100 logic previously hand-diffed in runs 3–5; no new engine logic | MATCHES / N/A | Analysis code does not alter the frozen engine behavior. No EXP-101 output-level golden trace is emitted. |
| Neutral report layers; no machine value labels (§4 REPORT-LAYERS; N1–N11) | `analysis.py:597-656,1007-1027` | DEVIATES | Helpers avoid prohibited value labels, but no `observed/ideal/interpretation` handoff is composed and no complete result artifact is written. |
| Live orchestration and required artifact (§4, §6 HARD) | `analysis.py:1007-1027` | **MISSING** | `--live` only loads every raid and prints `{"rows": n}`. It never calls `analyze_configurations`, never runs/blocks on the future destroy, and never writes the registered analysis result. |
| Deterministic, bounded, practical execution (§6 HARD; complexity budget) | `analysis.py:775-795,953-1004` | DEVIATES | Source loading materializes all bar marks and ~9.84M raids as Python objects. Per arm/stratum, the tripwire performs 5×10,000×2,000 = 100M deep-copy destroys, then repeats live destroys by seed. With all strata/arms this is not a viable bounded analysis path; no progress reporting exists. |
| Zero-cost disclosure on every results artifact (§9; N9) | `analysis.py:542-576`; `results/fixture_integrity.json:1-25` | DEVIATES | Fixture JSON omits `prohibited_claims` and `lifting`, and changes the canonical implication wording. The mandatory disclosure is not verbatim. |
| Powering strip / PSR | whole module | MATCHES / N/A | No MDE, power floor, `UNPOWERED`, cost read, or trade/leg mean. PSR remains N/A. |
| No local accounting / no Python price backtest | `analysis.py`; focused boundary check | MATCHES | `check_no_local_accounting` returned `ok=true`; no accounting or strategy simulation is defined. |

### Golden-trace diff

| Event | Expected from design | Implemented analysis behavior | Verdict |
|---|---|---|---|
| Pre-read fixture | 200 one-row clusters per arm; circular cluster bootstrap; +0.50 ATR, +3.6e12 ns, +0.25 proportion; every seed bites then collapses | Plant values and reported effects match, but outer resampling is iid rows, not the §4 circular cluster procedure | DEVIATES |
| Exact control group | Two rows sharing the declared fields/nullness form one derangeable group | Different profile reason strings split them into singleton groups; focused trace: `mapped_rows=0`, `void_no_derangement=2` | DEVIATES |
| Live configuration result | Emit all arm/comparator estimates, uncertainties, sensitivities, controls and hard integrity state | `--live` prints row count only | MISSING |
| T1–T3 engine events | Independent PREVIOUS_1H/ROLLING_7 rows; 2.00 price/ATR, 200 bps, 1h duration, strong=true | Frozen engine logic matched in prior QA; no implementation path re-emits or mutates it | MATCHES |

### Governance & boundary

- **Fresh-context independence:** PASS — dedicated subagent; no implementation authorship in this context.
- **Source gate and seals:** PARTIAL — focused `gate_first` verified 264 family-gate cells and all event-log hashes, but omitted the required per-cell result artifacts and config-hash equality.
- **TRAIN/holdout:** PASS for this QA — only TRAIN metadata/schema and previously retained fixture data were inspected; no TEST/holdout row was opened. Static live-path review found no path beyond the pinned TRAIN root, but causal row-order attestation is missing.
- **Registry/read accounting:** PASS — HYP-001 registered; 0 counted TEST reads; family remains `REGISTERED`.
- **Zero cost:** Source metadata/gate PASS; fixture results-document disclosure FAILS verbatim requirement.
- **Future destroy:** FAIL — population mismatch, extra grouping, ignored VOID/non-vacuity, and no enforced blocking outcome make the only hard control unsafe.
- **Neutrality/completeness:** FAIL — no full live report artifact or named report layers; no value labels were introduced.
- **Powering/PSR/XENA/screen conversion:** PASS/N/A.

### Issues

1. **CRITICAL — the live entry point does not execute the experiment.** `analysis.py:1007-1027` reads the retained source and exits after printing a row count. It never computes configuration contrasts, uncertainty, sensitivity, control evidence, or a blocking integrity result, and writes no live artifact. **Required fix:** add a deterministic live orchestrator that composes every registered row, runs integrity first, blocks affected observations, and writes a complete neutral result artifact. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
2. **CRITICAL — the hard future-destroy attestation compares different populations and does not block.** `analysis.py:725-817` bootstraps only arm+comparator when `joint=False`, while `:820-869` computes the live destroy on all configs; `:695-722` ignores missing derangements/non-vacuity and `:864-869` only nests status text. **Required fix:** use the identical declared population and estimator for raw, destroyed mean and both bootstrap SEs; make any missing mapping/statistic, vacuous mapping, or survival an enforced per-stratum/channel invalidity before value output. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
3. **HIGH — the control silently changes the registered grouping.** `analysis.py:317-325` adds profile fields/reasons and changes the five-bit null class; the focused trace produced two false singleton VOIDs. **Required fix:** implement the exact design grouping, while handling the binding ATR exclusion through an explicitly reconciled per-channel population rather than an undeclared grouping split. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
4. **HIGH — required source provenance/reconciliation is incomplete.** `analysis.py:880-950,958-1003` omits per-cell execution-gate reads, config-hash equality, `config/source_configuration` equality, metadata↔row cell identity, object/count reconciliation, and causal timestamp ordering. **Required fix:** attest each item before any estimator runs and fail closed on mismatch. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
5. **HIGH — uncertainty and output coverage are incomplete.** `analysis.py:597-656` runs only L=5, omits L=2/L=10 sensitivities, raw price/bps summaries, live destroyed 95% intervals, and separately named arm/comparator status, missingness and exclusion counts. **Required fix:** emit every predeclared field for every requested configuration without row suppression. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
6. **HIGH — the fixture validates a different bootstrap.** `analysis.py:399-454` uses iid row draws, while the live/design procedure is circular whole-cluster resampling. **Required fix:** run the fixture through the same bootstrap/control functions and exact L=5 mechanics used live; add regression assertions for population equality, singleton invalidity, survival blocking, and live orchestration. `FAILING_ARTIFACTS: analysis_code/analysis.py, python/tests/test_exp10x_analysis_contract.py`; `REQUIRED_SKILL: data-analyst`.
7. **HIGH — the implemented live algorithm is operationally infeasible and unbounded.** `analysis.py:775-795` performs 100M deep-copy destroy calls per arm/stratum before multiplication across the full grid; `:953-1004` materializes all marks and ~9.84M raids as Python dictionaries. **Required fix:** preserve the exact estimator while vectorizing/caching deterministic mappings, aggregating/projection-scanning source columns, bounding memory, and showing progress; prove equivalence with small golden fixtures. `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.
8. **HIGH — the emitted fixture artifact violates the mandatory zero-cost disclosure.** `analysis.py:545-551` and `results/fixture_integrity.json:4-11` omit two canonical fields and alter required text. **Required fix:** emit the canonical disclosure verbatim on fixture and future live artifacts, then regenerate the fixture result. `FAILING_ARTIFACTS: analysis_code/analysis.py, results/fixture_integrity.json`; `REQUIRED_SKILL: data-analyst`.

### Commands run

```text
PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/test_exp10x_analysis_contract.py
# 16 passed in 0.32s
PYTHONPATH=python/src python/.venv/bin/python -m py_compile python/experiments/EXP-101/analysis_code/analysis.py
PYTHONPATH=python/src python/.venv/bin/python - <gate_first + check_no_local_accounting>
# verified_cells=264; no-local-accounting ok=true
PYTHONPATH=python/src python/.venv/bin/python - <two-row exact-group trace>
# mapped_rows=0; void_no_derangement=2 (expected one 2-row design group)
sha256sum python/experiments/EXP-{100,101}/results/estimand_validation.json
# byte-identical: 1593851873c318f3040fe1f04cedb8460dcb86470a296821548015079ffd3488
```

## QA run 7 — 2026-08-15T05:39:26Z — mode: subagent — HEAD 99bc9bd52812471281e806871275b16ac26fc226

Verdict: **REVISE**

Scope: fresh design-first analysis-readiness review of the current dirty workspace. Only
retained EXP-100 TRAIN artifacts were opened; no TEST/holdout, live analysis, Nautilus run,
or implementation/design edit occurred. Dirty state before append: modified EXP-101/102
adapters; untracked `test_exp101/102/103_analysis_live.py`.

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Frozen TRAIN fence and source identity (§1) | `source.py:111-276`; direct 264-cell validation | **DEVIATES** | Validator expects absent numeric `train_end_ns` instead of pinned `train_end_utc` and treats cell-local `raid_id` as globally unique. It returned `VOID_FENCE_BOUNDARY` + `VOID_DUPLICATE_OBJECT_ID` on 9,840,478 accepted rows. Independent audit found zero within-cell and zero `(source_cell, raid_id)` duplicates. Live cannot start. |
| All-configuration destroy donors (§5) | `adapter.py:224-251`; new regression | **DEVIATES** | Shared population filters to current arm+comparator. Design pools all 11 configs. Expected donor group 2,200; observed 400. |
| Independent arm/comparator bootstrap (§4) | `statistics.py:111-195` | **DEVIATES** | Shared bootstrap jointly resamples one combined cluster sequence; EXP-101 requires independent resampling of the distinct configuration populations. |
| Exact 10,000 outer × 2,000 inner destroys (§5) | `adapter.py:295-343` | **DEVIATES** | Code destroys once, averages outcomes, bootstraps the average, then combines SEs by `hypot`. Design rebuilds 2,000 destroys inside every outer population. Literal shared-path trace: code 1.229006032152678 vs registered 0.7083849310412494. |
| Per-control hard propagation and complete output (§5 HARD) | `adapter.py:344-386`; `runtime.py:83-99` | **DEVIATES** | Individual failed controls do not enter overall reasons if a companion passes; failed rows are silently skipped. Null/non-null duration alias mismatch is missed and all 2,000 destroyed contrasts are not emitted. |
| Output layers / boundedness (§4–6) | `adapter.py:388-495`; `destroy.py:137-215` | PARTIAL | Five channels, L=2/5/10, census and report layers exist. Memory is bounded only for the non-registered approximation; exactness plus production runtime is unproved. |

### Golden-trace diff

- T1–T3 frozen engine events: MATCHES prior hand trace; engine source is unchanged.
- Control plant: DEVIATES — pair-only donors, joint rather than independent clusters, non-nested SE.
- Live handoff: MISSING/FAIL-CLOSED — accepted TRAIN source is rejected before analysis.

### Governance & boundary

- Fresh context / TRAIN-only / no TEST-holdout: PASS.
- EXP-100 gate: PASS (`blocking_pass=true`, 264 cells); copied gates byte-identical.
- Zero cost, no local accounting, no Python price backtest: PASS (`check_no_local_accounting ok=true`).
- Mandatory declarations, powering strip, PSR N/A: PASS.
- Source, future-destroy fidelity, completeness, practical exact execution: FAIL.

### Issues

1. **CRITICAL:** fix `source.py:181-184,254-266` to validate the pinned UTC fence and composite `(source_cell, raid_id)` identity. `REQUIRED_SKILL: data-analyst`.
2. **CRITICAL:** pool all 11 config donors and independently resample arm/comparator clusters. `FAILING_ARTIFACTS: adapter.py, EXP-101 adapter`; `REQUIRED_SKILL: data-analyst`.
3. **CRITICAL:** implement/prove an exactly equivalent bounded nested 10,000×2,000 estimator; current numeric parity fails. Route to `quant-designer` if semantics must change.
4. **HIGH:** propagate every failed control, preserve explicit invalid rows/reasons, catch alias nullness mismatch, and emit every destroyed contrast. `FAILING_ARTIFACTS: adapter.py, runtime.py`.

Focused suite: **47 passed, 9 failed**; EXP-101 all-donor regression failed.


## QA run 8 — 2026-08-15T22:34:08Z — mode: subagent — HEAD 6d816e8603a6b4d9c7edd86a13639d582a7f4958

Verdict: **REVISE**

Scope: fresh-context design-to-code fidelity review of EXP-101's analysis implementation
against the frozen AMENDMENT-14 design. Only retained EXP-100 TRAIN artifacts and the
EXP-101 `analysis_code/` were inspected; no TEST/holdout access, no Nautilus run, no
design or implementation edits. The fixture was executed to verify the integrity pipeline.

Reviewed dirty state before append: `M python/experiments/EXP-101/results/fixture_integrity.json`

### Prior-finding resolution audit

| Prior issue (QA run 7) | Current verdict | Evidence |
|---|---|---|
| Validator expects absent `train_end_ns` field | RESOLVED | `source.py:143` now reads `train_end_utc` and converts; fence check passes. |
| Cell-local `raid_id` treated as globally unique | RESOLVED | `source.py:178-180` checks uniqueness per cell directory. |
| Missing per-cell execution-gate reads | PARTIAL | `source.py:158-165` reads family gate; cell gates reconciled by name but not all 264 individually re-verified in the focused trace. |
| Fixture topology mismatches design | **PERSISTS** | `adapter.py:126-173` `make_fixture_frame` uses synthetic timestamps and `L-{idx}` level_ids; design §5 requires specific epoch, `FIXTURE-{arm}-level-{i:04d}`, seed=4 permutation. |
| Cluster bootstrap resamples combined pool | **PERSISTS** | `statistics.py:240-288` draws from combined arm+comparator clusters; design §4 requires independent resampling per population. |
| Destroy outer SE adds Monte Carlo term | **PERSISTS** | `adapter.py:353-358` `destroyed_outer_se = hypot(destroyed_data_se, destroyed_mapping_se)`; design §5 tripwire specifies `bootstrap_SE_mean_destroyed = std_b(m_destroy[s,b])` only. |
| Live analysis entry point incomplete | **PERSISTS** | `analysis.py:1007-1027` `--live` prints row count only; no orchestration of contrasts, sensitivities, controls, or result artifact. |
| Zero-cost disclosure verbatim | RESOLVED | Fixture output matches canonical disclosure exactly (verified). |

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Gate-first source validation; 264 passing cells; per-cell execution gates; config-hash equality; event-log hashes; causal fence (§1) | `source.py:111-276` `validate_source_contract` | PARTIAL | Family gate and cell-gate reconciliation by name implemented; per-cell `blocking_pass`, `config_hash`, `event_log_sha256`, `NO_COST_CHARGED`, fence boundary all checked. Causal timestamp ordering (`raid_ts_ns ≤ sweep_ts_ns ≤ return_ts_ns ≤ confirmation_ts_ns ≤ endpoint_ts_ns`) validated. **Gap**: metadata↔row identity for `archive_symbol`, `timeframe`, `confirmation_method`, `confirmation_reference`, `config` not explicitly asserted after parquet read (only unique-value check on lazy frame). |
| Frozen schema: `config`/`source_configuration`, IDs, outcome fields; `swing_duration_ns` canonical, `duration_ns` byte-equal alias; `pre_mfe_retrace` excluded (§1) | `adapter.py:997-998` (assert); `adapter.py:44-47` (common evidence) | MATCHES | Assertion and mismatch counter present. |
| Configuration populations: 11 configs, Family A/B/C fixed baselines (§3) | `analysis.py:44-51` `Adapter.contrasts` | MATCHES | Exact match to design catalogue and comparator mapping. |
| Population: `status==COMPLETED ∧ primary_attribution ∧ primary_completed`; ATR-undefined excluded from `swing_atr`/`strong_move` (§3) | `adapter.py:409-418` `_channel_frame` | MATCHES | Filter logic matches design exactly. |
| Estimators: arm-minus-comparator mean `swing_atr`, mean `swing_duration_ns`, unpaired `strong_move` proportion; median disclosures (§3–4) | `statistics.py:80-110` `estimate_contrast`; `adapter.py:597-656` `analyze` | MATCHES | Contrast orientation, median dict, and unpaired proportion (mean of booleans) correct. |
| Uncertainty: circular cluster bootstrap, `L_eff=min(max(1,L), n_clusters-1)`, independent arm/comparator resampling, 10k resamples, seeds 0–4, numpy linear quantile, L=5 default + L=2/10 sensitivity (§4) | `statistics.py:130-185` `circular_cluster_indices`; `statistics.py:240-288` `clustered_contrast_bootstrap`; `statistics.py:330-350` `block_sensitivity` | **DEVIATES** | Circular draw and `L_eff` correct; seeds, resamples, quantile method correct. **Critical deviation**: bootstrap draws from combined arm+comparator cluster pool (§4: "arm and fixed-baseline clusters are distinct configuration populations and are resampled independently"). Current code pools all clusters then draws, varying arm/comparator counts per replicate. |
| Cross-config destroy grouping: exact stratum + `status` + `primary_completed` + 5-bit outcome-nullness class; config pooled; 2,000 derangements (zero fixed points) (§5) | `analysis.py:30-37` `CONTROL_GROUP_COLUMNS`, `CONTROL_NULL_COLUMNS`; `destroy.py:140-200` `build_destroy_mappings` | MATCHES | Grouping columns and nullness class match design; `derange_indices` rejects fixed points; singleton groups → `VOID_NO_DERANGEMENT`. |
| Hard tripwire: outer bootstrap 10k×5 seeds; same population & estimator for raw, destroyed mean, both SEs; `INTEGRITY_Z=2.8`; `abs(D_raw) > 2.8×SE_raw ⇒ abs(m_destroy) ≤ 2.8×SE_destroyed` else `VOID_FUTURE_DESTROY_SURVIVAL`; missing/failed derangement = invalidity (§5) | `adapter.py:340-370` `integrity`; `destroy.py:260-330` `future_destroy_attestation` | **DEVIATES** | Population/estimator identity enforced (`population_match`). Raw bootstrap SE correct. **Deviation**: `destroyed_outer_se = hypot(destroyed_data_se, destroyed_mapping_se)` adds Monte Carlo SE from 2,000 destroys; design specifies `bootstrap_SE_mean_destroyed = std_b(m_destroy[s,b])` only (the bootstrap SE of the destroyed mean across outer replicates). The extra term makes the inequality harder to fail (wider destroyed SE), weakening the tripwire. |
| Fixture topology: 200 rows/arm, one-row clusters, `FIXTURE-{arm}-level-{i:04d}`, epoch `1_700_000_000_000_000_000 + i*900_000_000_000`, seed=4 permutation, `raid_id=fixture-raid-{pos:04d}`, outer bootstrap=10 (§5) | `adapter.py:126-173` `make_fixture_frame` | **DEVIATES** | Uses `R-{idx}-{i}` / `L-{idx}-{i}` IDs, synthetic timestamps `100+i*10`, no seed=4 permutation step, `config=FIXTURE_CONFIG` for all. The fixture does not exercise the declared cluster bootstrap (L=5 with one-row clusters still changes adjacent selection) because the shared fixture is generic. |
| Golden trace T1–T3: independent PREVIOUS_1H/ROLLING_7 cells, inclusive return, primary completion, 2.00 price/ATR, 200 bps, 1h duration, `strong_move=true` (§7) | Frozen EXP-100 logic (`processor.py:285-328,400-458,462-612`); hand-diffed in prior QA | MATCHES | Engine behavior matches; no EXP-101 analysis-level golden trace emitted (no live run). |
| Report layers: observed/ideal/interpretation/analyst_boundary; no machine value labels (§4) | `adapter.py:620-630` `analyze` output dict | MATCHES | Fields present; `interpretation` string correct. |
| Amendment ledger: 2L/3T/8N, no machine qualifier, no row hiding (§8) | `design.md:214-245` | MATCHES | Ledger correct; design declares no selection gates. |
| Zero-cost disclosure: canonical verbatim on every artifact (§9) | `contract.py:10-25` `ZERO_COST_DISCLOSURE`; `fixture_integrity.json` | MATCHES | Fixture output verified verbatim. |

### Golden-trace diff

| Event | Expected from design | Implemented behavior | Verdict |
|---|---|---|---|
| Pre-read fixture | 200 one-row clusters/arm; circular cluster bootstrap L=5; +0.50 ATR, +3.6e12 ns, +0.25 proportion; every seed bites then collapses | Plant values match; **bootstrap uses combined pool, not independent arm/comparator resampling**; outer bootstrap=10 (design) vs 10k (live) | DEVIATES |
| Exact control group | Two rows sharing declared fields/nullness form one derangeable group | `build_destroy_mappings` uses exact design grouping; verified in fixture (`group_sizes=[400]`, `moved_rows=400`, `fixed_points=0`) | MATCHES |
| Live configuration result | All arm/comparator estimates, uncertainties (L=5 + L=2/10), status/censor/missingness per arm, control evidence, hard integrity state | `--live` prints `{"rows": n}` only; no orchestration, no result artifact | MISSING |
| T1–T3 engine events | Independent PREVIOUS_1H/ROLLING_7 rows; 2.00 price/ATR, 200 bps, 1h duration, strong=true | Frozen engine logic matched; no implementation path re-emits or mutates | MATCHES |

### Governance & boundary

- **Fresh-context independence:** PASS — dedicated `subagent`; no EXP-101 implementation authorship in this context.
- **Source gate and seals:** PARTIAL — `validate_source_contract` checks family gate, cell-gate reconciliation, config-hash, event-hash, zero-cost, fence boundary, causal ordering, schema, duplicate object IDs per cell. **Missing**: explicit metadata↔row identity assertion after parquet collection for `archive_symbol`, `timeframe`, `confirmation_method`, `confirmation_reference`, `config`.
- **TRAIN/holdout:** PASS for this QA — only TRAIN metadata/schema and fixture data inspected; no TEST/holdout row opened. Static review confirms no live path beyond pinned TRAIN root.
- **Registry/read accounting:** PASS — `CF-LIQSWP-001/HYP-001` registered; 0 candidate slots; 0 counted TEST reads; family `REGISTERED`.
- **Zero cost:** PASS — source metadata/gate `NO_COST_CHARGED`; fixture artifact disclosure verbatim canonical; no cost function imports or calls in analysis code.
- **Future destroy:** **FAIL** — population/estimator identity correct; derangement correct; **but** outer SE adds Monte Carlo term (weakens tripwire), bootstrap pools arm/comparator (changes null distribution), and live orchestration absent so tripwire never actually blocks.
- **Neutrality/completeness:** FAIL — no live result artifact; `--live` does not execute the experiment.
- **Powering/PSR/XENA/screen conversion:** PASS/N/A — no research MDE/power/floor, no trade/leg mean, no XENA route, no screen-money claim.
- **One `BacktestNode`:** PASS — EXP-100 metadata `one_backtest_node=true`; EXP-101 analysis-only, no new engine process.
- **Derangement:** PASS — `derange_indices` rejection-samples zero fixed points; singleton groups produce `VOID_NO_DERANGEMENT`.

### Issues

1. **CRITICAL — Cluster bootstrap does not resample arm and comparator independently.**  
   **Design:** §4 "arm and fixed-baseline clusters are distinct configuration populations and are resampled independently."  
   **Code:** `statistics.py:240-288` `clustered_contrast_bootstrap` builds a single cluster list from the combined `PopulationView` and draws circular blocks from it.  
   **Why it matters:** The bootstrap null distribution is wrong; arm/comparator cluster counts vary randomly per replicate instead of being drawn independently, altering the contrast variance and interval coverage.  
   **Required fix:** Refactor `clustered_contrast_bootstrap` (or add a variant) to accept separate arm/comparator cluster arrays and draw independently per the design. Prove equivalence on fixtures.  
   **FAILING_ARTIFACT:** `python/src/xen/liqswp_analysis/statistics.py`; **REQUIRED_SKILL:** `experiment-developer` / `data-analyst`.

2. **CRITICAL — Destroy outer SE incorrectly includes Monte Carlo term, weakening the hard tripwire.**  
   **Design:** §5 tripwire: `bootstrap_SE_mean_destroyed[s] = std_b(m_destroy[s,b], ddof=1)` (bootstrap SE of destroyed mean across outer replicates only).  
   **Code:** `adapter.py:353-358` `destroyed_outer_se = hypot(destroyed_data_se, destroyed_mapping_se)` where `destroyed_mapping_se = std(destroy_run.estimates)/√n_destroy`.  
   **Why it matters:** The extra Monte Carlo term inflates the destroyed SE, making `abs(m_destroy) ≤ INTEGRITY_Z × SE_destroyed` easier to satisfy. A surviving contrast could pass when it should be flagged `VOID_FUTURE_DESTROY_SURVIVAL`.  
   **Required fix:** Use `destroyed_data_se` alone (the bootstrap SE of the destroyed mean) as `destroyed_bootstrap_se` in the attestation. Remove the `hypot` combination.  
   **FAILING_ARTIFACT:** `python/src/xen/liqswp_analysis/adapter.py`; **REQUIRED_SKILL:** `experiment-developer` / `data-analyst`.

3. **CRITICAL — Live entry point does not execute the experiment.**  
   **Design:** §4, §6 HARD require complete neutral result artifact with all contrasts, uncertainties, sensitivities, control evidence, and integrity state.  
   **Code:** `analysis.py:1007-1027` `main()` `--live` loads source and prints row count only.  
   **Why it matters:** The experiment cannot be run; no result artifact is produced for the operator's execution gate.  
   **Required fix:** Implement a deterministic live orchestrator that (a) runs integrity first, (b) blocks affected strata/channels, (c) computes all registered contrasts/sensitivities, (d) composes the neutral report layers, (e) writes the complete result artifact with canonical zero-cost disclosure.  
   **FAILING_ARTIFACT:** `python/experiments/EXP-101/analysis_code/analysis.py`; **REQUIRED_SKILL:** `experiment-developer`.

4. **HIGH — Fixture topology does not match the design's FIXTURE-TOPOLOGY specification.**  
   **Design:** §5 `FIXTURE-TOPOLOGY` block specifies exact timestamps, `level_id` format, seed=4 permutation, `raid_id` format, outer bootstrap=10.  
   **Code:** `adapter.py:126-173` `make_fixture_frame` uses generic synthetic data (`R-{idx}-{i}`, `L-{idx}-{i}`, timestamps `100+i*10`, all `config=FIXTURE_CONFIG`).  
   **Why it matters:** The fixture does not validate the exact cluster bootstrap mechanics (L=5 with one-row clusters) or the declared derangement seeding. A passing fixture gives false confidence.  
   **Required fix:** Either (a) make the shared `make_fixture_frame` configurable to match EXP-101's declared topology, or (b) override `fixture_frame` in EXP-101's `Adapter` to construct the exact design fixture. Run the fixture through the production integrity path and assert regression on all control channels.  
   **FAILING_ARTIFACTS:** `python/src/xen/liqswp_analysis/adapter.py`, `python/experiments/EXP-101/analysis_code/analysis.py`; **REQUIRED_SKILL:** `experiment-developer`.

5. **HIGH — Source provenance: metadata↔row identity not explicitly asserted post-read.**  
   **Design:** §1 "seal: retain each cell's config_hash and event_log_sha256; require emission_contract_version=nautilus-emission-v1..." and gate-first rule.  
   **Code:** `source.py:180-190` checks unique values on lazy frame; no row-level assertion after collection that every row matches the cell's declared `archive_symbol`, `timeframe`, `confirmation_method`, `confirmation_reference`, `config`.  
   **Why it matters:** A schema-valid but identity-mismatched parquet would pass current checks.  
   **Required fix:** After `collect(engine="streaming")`, assert `frame.filter(pl.col(c) != expected).height == 0` for each identity column per cell.  
   **FAILING_ARTIFACT:** `python/src/xen/liqswp_analysis/source.py`; **REQUIRED_SKILL:** `experiment-developer`.

6. **HIGH — Zero-cost disclosure verified on fixture but live artifact path untested.**  
   **Design:** §9 "canonical disclosure on every results artifact."  
   **Code:** `contract.py:10-25` `ZERO_COST_DISCLOSURE` included in `AnalysisResult.to_dict()`; fixture output verified verbatim. Live artifact never produced.  
   **Required fix:** Resolved by Issue 3 (live orchestrator will emit the disclosure via `AnalysisResult.to_dict()`).  
   **FAILING_ARTIFACT:** `python/experiments/EXP-101/analysis_code/analysis.py`; **REQUIRED_SKILL:** `experiment-developer`.

### Summary

**REVISE.** The frozen source, design, golden trace (engine level), registry, fence, and zero-cost disclosure are consistent. The analysis implementation has three critical fidelity deviations (independent bootstrap, destroy SE, live orchestration) and two high-severity gaps (fixture topology, source identity assertion) that must be resolved before the operator's execution gate. The fixture passes its internal integrity checks but validates a different bootstrap and destroy SE than the design specifies.

---

**Commands run during this review**

```text
PYTHONPATH=python/src python3 -m python.experiments.EXP-101.analysis_code.analysis --fixture
# → fixture_integrity.json generated; all controls blocking_pass=true; fixed_points=0; population_match=true
PYTHONPATH=python/src python3 -c "from xen.liqswp_analysis.source import validate_source_contract; print('import OK')"
# → source validation module loads
PYTHONPATH=python/src python3 -c "
from pathlib import Path
import json
fixture = json.loads(Path('python/experiments/EXP-101/results/fixture_integrity.json').read_text())
disc = fixture['zero_cost_disclosure']
canonical = {'heading':'ZERO-COST-DISCLOSURE','cost_model':'NO_COST_CHARGED','spread':'not modeled','commissions':'not modeled','swaps/funding':'not modeled','implication':'every figure in this document is gross and cost-free; no spread, commission, or swap enters any calculation. Realised results would differ (likely worse) under any real cost schedule.','prohibited_claims':'fully-net, cost-complete, tradable, deployable','lifting':'only an explicit operator directive may introduce a cost model for a scoped experiment; the directive is recorded in that experiment\'s design.md.'}
print('Zero-cost verbatim:', disc == canonical)
"
# → True
git rev-parse HEAD
# → 6d816e8603a6b4d9c7edd86a13639d582a7f4958
git status --short
# → M python/experiments/EXP-101/results/fixture_integrity.json
```


## QA run 7 — 2026-08-15T00:00:00Z — mode: subagent — HEAD 8127c23e9d034af967f7ecc1f1e7508a3473ef8d

Verdict: **REVISE**

Scope: Fresh-context pre-execution review of EXP-101 (CF-LIQSWP-001/HYP-001) analysis implementation against the frozen EXP-100 AMENDMENT-14 TRAIN emission. No EXP-100 modification, execution, rerun, or re-emission; no EXP-101 live execution; no TEST or holdout access. Reviewed git state was clean (no dirty files).

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| **§1 Frozen source authority & gate-first** | `source.py:155-348` `validate_source_contract` | MATCHES | Family gate checked before any source rows; 264 cells verified; config_hash, event_log_sha256, NO_COST_CHARGED, one_backtest_node, nautilus-emission-v1, Nautilus=1.230.0 all validated. |
| **§1 TRAIN fence & UTC fence** | `source.py:112-126` `_validate_utc_fence`; `source.py:168` | MATCHES | `train_end_ns` (1_700_611_200 * 1_000_000_000) validated against `train_end_utc` "2023-11-22T00:00:00Z". |
| **§1 Composite ID uniqueness** | `source.py:129-152` `_validate_composite_uniqueness`; `source.py:319-337` | MATCHES | `(source_cell, raid_id)` uniqueness checked across all 264 cells. |
| **§1 Causal timestamp provenance** | `source.py:275-297` | MATCHES | `raid_ts_ns ≤ sweep_ts_ns ≤ return_ts_ns ≤ confirmation_ts_ns ≤ endpoint_ts_ns` validated per cell. |
| **§1 Schema/object/count reconciliation** | `source.py:234-268` | MATCHES | Required columns present; row counts match metadata; `source_configuration == config`; no rows after TRAIN fence. |
| **§1 Binding ATR_UNDEFINED exclusion** | `adapter.py:205-215` `_channel_frame` | MATCHES | `swing_atr` and `strong_move` exclude rows where `profile_undefined_reason == "ATR_UNDEFINED"`. |
| **§2 Mechanism & object identity** | `design.md:47-67`; `adapter.py:250` `cluster_ids=level_id` | MATCHES | Level-linked raid is measurement object; clustering by `level_id`; no orders/fills. |
| **§3 Configuration strata & fixed comparators** | `analysis.py:126-135` `contrasts`; `analysis.py:136-142` `stratum_columns` | MATCHES | 11 configs in 3 families; fixed comparators (PREVIOUS_1H, PREVIOUS_ASIA, ROLLING_7); strata exclude `config` so contrasts are within-stratum. |
| **§3 Population & censoring rules** | `adapter.py:205-215` `_channel_frame` | MATCHES | Primary population = COMPLETED & primary_attribution & primary_completed; failed/non-primary/censored/null/thin rows remain in census. |
| **§3 Primary estimators** | `analysis.py:126-135` `contrasts`; `adapter.py:127-130` `control_channels` | MATCHES | Mean `swing_atr`, mean `swing_duration_ns`, unpaired `strong_move` proportion difference. |
| **§4 Independent arm/comparator bootstrap** | `statistics.py:220-276` `clustered_contrast_bootstrap` `independent_arms=True` | MATCHES | Arm and comparator clusters resampled independently per design; `circular_cluster_indices` implements circular block bootstrap with `L_eff = min(max(1,L), n_clusters-1)`. |
| **§4 Block lengths L=2,5,10** | `statistics.py:336-354` `block_sensitivity`; `adapter.py:468-474` | MATCHES | Sensitivities computed for all three block lengths; L=5 is primary. |
| **§4 Empty arm handling** | `statistics.py:203-214` | MATCHES | Returns `EMPTY_ARM` reason with counts, null estimate/interval; row not removed. |
| **§4 Report layers (observed/ideal/interpretation)** | `adapter.py:489-502` | MATCHES | Output includes `observed`, `ideal`, `interpretation` fields; no machine value labels. |
| **§4 No prohibited value labels** | `adapter.py:489-502`; `contract.py:50-60` | MATCHES | No `SUPPORTED`, `WASH`, `CONTRADICTED`, `WORTH_EXPLORING`, `NOT_WORTH`, `INCONCLUSIVE` in output. |
| **§5 Cross-config destroy grouping** | `destroy.py:230-256` `stream_destroy_control` | MATCHES | Groups by `archive_symbol × timeframe × confirmation_method × confirmation_reference × side × status × primary_completed × 5-bit nullness class`; configuration pooled within group. |
| **§5 Derangement (zero fixed points)** | `destroy.py:72-85` `derange_indices`; `destroy.py:241-246` | MATCHES | Rejection sampling until `perm[i] != i` for all movable rows; singleton groups VOIDed. |
| **§5 Singleton VOID** | `destroy.py:237-246` | MATCHES | Groups with `n<2` produce `VOID_SINGLETON_GROUP`; rows not moved. |
| **§5 Destroy disclosure fields** | `adapter.py:397-419` control record evidence | PARTIAL | Includes raw contrast, destroyed draws, mean, interval, collapse_ratio, fixed_points, moved_rows, moved_eligible_values. Missing: empirical 95% destroyed interval for live (only fixture has it). |
| **§5 Exact nested 10k×2k destroy** | `destroy.py:507-532` `compute_exact_nested_destroy_se` | **MISSING** | Function is a placeholder (`pass`). Design requires: for each seed s=0..4, 10k bootstrap populations; for EVERY population b, recompute D_raw[s,b] AND all 2k deranged contrasts D_destroy[s,b,d]; compute m_destroy[s,b]; bootstrap_SE_raw[s]=std_b(D_raw); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy). Current implementation computes destroy contrasts only ONCE on original population, not per bootstrap population. |
| **§5 Fixture topology & plants** | `adapter.py:77-116` `make_fixture_frame` | DEVIATES | Design specifies explicit plants: swing_atr baseline 0.90/1.10 vs arm 1.40/1.60 (+0.50); duration baseline 3e12/4.2e12 vs arm 6.6e12/7.8e12 (+3.6e12 ns); strong_move baseline 1/4 vs arm 1/2 (+0.25). Shared fixture creates gradient values across 11 configs, not the two-arm explicit plants. |
| **§5 Nullness class: `duration_ns` vs `swing_duration_ns`** | `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns` | DEVIATES | Design §5 defines 5-bit nullness class as `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))`. Code uses `swing_duration_ns` (canonical). Byte-equal in practice but technically deviates from declared field name. |
| **§6 Sample size & complexity** | `design.md:164-177`; `adapter.py` | MATCHES | No minimum n; all rows retained; channels declared with sigma_denominator; 1 independent analysis module. |
| **§6 Hard/informative split** | `design.md:179-186`; `contract.py` `IntegrityStatus` | MATCHES | Hard blocks: gate-first, fence, causality, schema, no-local-accounting, deterministic, ATR exclusion, future-destroy validity, zero-cost. Informative: operator judges all effects. |
| **§7 Golden trace T1–T3** | `design.md:182-195`; EXP-100 `processor.py` | MATCHES | Hand-verified: independent PREVIOUS_1H/ROLLING_7 cells; inclusive return; primary attribution; swing_price=2.00, swing_atr=2.00, swing_bps=200, swing_duration_ns=3.6e12, strong_move=true. |
| **§8 Amendment ledger & final null** | `design.md:198-245` | MATCHES | 2L/3T/8N; no machine qualifier; no row hiding; F02/F04/F06 N/A; F07 satisfied. |
| **§9 Zero-cost disclosure** | `contract.py:10-25` `ZERO_COST_DISCLOSURE`; fixture output | MATCHES | Canonical text verbatim; `NO_COST_CHARGED`; no prohibited claims. |
| **Failed-control propagation** | `adapter.py:426-431` | MATCHES | Failed control reasons collected into overall integrity reasons; `VOID_FUTURE_DESTROY_SURVIVAL` blocks affected stratum/channel. |
| **Live orchestration & integrity gating** | `runtime.py:75-99` `_execute`; `analysis.py:233-238` | MATCHES | `--live` runs `run_live` → `adapter.integrity` → blocks `analyze` if integrity fails → atomic write. |

### Golden-trace diff

| Event | Expected from design | Implemented logic | Verdict |
|---|---|---|---|
| T1 — Separate PREVIOUS_1H/ROLLING_7 cells at 100.00 | Each starts own raid; excursion 1.20; count 0 | `processor.py:400-458` cell-local level/raid identity; side-aware excursion | MATCHES |
| T2 — Inclusive 100.00 return; expected-side 1H close | Return recorded; primary_attribution=true per cell | `processor.py:285-328,462-522` inclusive return; cell-local primary selection | MATCHES |
| T3 — Opposing endpoint at 98.00 | swing_price=2.00, swing_atr=2.00, swing_bps=200, duration=3.6e12 ns, strong_move=true | `processor.py:540-612` terminal arithmetic; duration alias implemented | MATCHES |
| Fixture plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion per design plants | Shared fixture uses gradient values across 11 configs | DEVIATES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation authorship in this context.
- **Gate-first:** PASS — `validate_source_contract` checks family gate (264 cells, `blocking_pass=true`) and all 264 per-cell gates before any parquet read.
- **TRAIN/holdout:** PASS — `train_end_ns` fence enforced; `VOID_AFTER_TRAIN` blocks any row beyond 2023-11-22T00:00:00Z; no TEST/holdout paths in code.
- **Registry:** PASS — `CF-LIQSWP-001/HYP-001` registered; 0 candidate slots; 0 counted TEST reads.
- **No Python backtest/local accounting:** PASS — `check_no_local_accounting` would pass; no accounting primitives; no strategy backtest in EXP-101.
- **One BacktestNode:** PASS — EXP-101 is analysis-only; EXP-100 metadata attests `one_backtest_node=true`.
- **Derangement:** PASS — `derange_indices` uses rejection sampling; `VOID_FIXED_POINTS` if any.
- **Zero cost:** PASS — Canonical disclosure verbatim; `NO_COST_CHARGED` in all metadata.
- **No research powering:** PASS — No MDE, power curves, `UNPOWERED`, detection floors. Only `INTEGRITY_Z=2.8` for validity.
- **PSR:** N/A — No trade/leg bps series.
- **Screen conversion/XENA:** N/A.
- **Battery rules:** PASS — No adaptive selection, capped read, exit selection, or phase-shift gate.

### Issues

1. **HIGH — Exact nested 10k×2k destroy not implemented.**
   **Design:** §5 "outer bootstrap: for each seed s=0..4, generate 10,000 cluster-bootstrap populations... For every population b, recompute the raw contrast D_raw[s,b] and all 2,000 deranged contrasts D_destroy[s,b,d]."
   **Code:** `destroy.py:507-532` `compute_exact_nested_destroy_se` is a placeholder (`pass`). `adapter.py:323-378` computes destroy contrasts only once on the original population, then bootstraps the *average* destroyed values. The design requires per-bootstrap-population destroy recomputation.
   **Required change:** Implement the exact nested destroy in `adapter.integrity` (or a called function): for each seed, for each of 10,000 bootstrap draws, resample clusters, then run all 2,000 derangements on that resampled population. Compute `m_destroy[s,b]` per draw, then `bootstrap_SE_mean_destroyed[s] = std_b(m_destroy[s,b])`.
   **Failing artifact:** `python/src/xen/liqswp_analysis/destroy.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

2. **HIGH — Fixture plants deviate from design specification.**
   **Design:** §5 FIXTURE-TOPOLOGY specifies 200 rows per arm (BASELINE/ARM) with explicit plants: swing_atr baseline 0.90/1.10 vs arm 1.40/1.60 (+0.50); duration baseline 3e12/4.2e12 vs arm 6.6e12/7.8e12 (+3.6e12 ns); strong_move baseline 1/4 vs arm 1/2 (+0.25).
   **Code:** `adapter.py:77-116` `make_fixture_frame` creates 200 rows × 11 configs with gradient values; no explicit two-arm plants.
   **Required change:** Either update the design to match the implemented multi-config fixture (with documented rationale), or implement a dedicated two-arm fixture matching the design's explicit plants for the pre-read smoke test.
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `quant-designer` (if design change) or `experiment-developer` (if implementation change).

3. **MEDIUM — Nullness class uses `swing_duration_ns` instead of declared `duration_ns`.**
   **Design:** §5 "nullness class is the five-bit tuple (is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias of swing_duration_ns."
   **Code:** `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns`; `adapter.py:132` inherits `CONTROL_NULL_COLUMNS = CHANNELS`.
   **Why it matters:** The design explicitly names `duration_ns` in the nullness class definition. While byte-equal in the frozen emission, the code should reference the declared alias name for traceability.
   **Required change:** Change `CONTROL_NULL_COLUMNS` to use `duration_ns` (or add both and verify equality), and update the 5-bit class computation accordingly.
   **Failing artifact:** `python/experiments/EXP-101/analysis_code/analysis.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

4. **MEDIUM — Missing `swing_price`/`swing_bps` source-field summaries in analysis output.**
   **Design:** §4 "Report counts, missingness, status/censor composition, mean, median, direct difference, interval, seed range, and every requested configuration. Raw `swing_price` and `swing_bps` are source-field summaries, not separate hard tripwire estimands."
   **Code:** `adapter.py:489-502` `analyze` method outputs medians for all channels but does not include raw mean/summary statistics for `swing_price` and `swing_bps` in the result rows.
   **Required change:** Add `swing_price` and `swing_bps` mean/median summaries to the analysis output (can be in `observed` or as separate fields).
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

5. **LOW — Empirical 95% destroyed interval missing from live control disclosure.**
   **Design:** §5 "disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical 95% interval; collapse_fraction..."
   **Code:** `adapter.py:397-419` fixture control records include `destroyed_interval` (from `future_destroy_attestation`), but live control path uses `destroyed_outer_se` (hypot combination) and does not compute the empirical quantile interval from the 2,000 destroyed contrasts.
   **Required change:** Ensure live control records include the empirical 95% interval from the 2,000 destroyed contrasts (not just the bootstrap SE interval).
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

### Summary

**REVISE.** The EXP-101 analysis implementation correctly implements the majority of the design: frozen source validation, independent arm/comparator bootstrap, derangement-based cross-configuration destroy, singleton VOID, UTC fence + composite ID, failed-control propagation, live orchestration with integrity gating, and neutral report layers. The golden trace matches the frozen EXP-100 logic.

Two **HIGH** issues block execution readiness:
1. The exact nested 10k×2k destroy (per-bootstrap-population destroy recomputation) is not implemented — the current code computes destroy contrasts only once on the original population.
2. The fixture plants do not match the design's explicit two-arm plant specification.

Three **MEDIUM/LOW** issues should be addressed before execution:
3. Nullness class field name mismatch (`duration_ns` vs `swing_duration_ns`).
4. Missing `swing_price`/`swing_bps` source-field summaries in output.
5. Live control disclosure missing empirical 95% destroyed interval.

Route to `experiment-developer` for implementation fixes (issues 1, 3, 4, 5) and `quant-designer` for design/implementation alignment on fixture plants (issue 2).

## QA run 10 — 2026-08-16T23:30:55Z — mode: subagent — HEAD 8127c23e9d034af967f7ecc1f1e7508a3473ef8d

Verdict: **REVISE**

Scope: fresh-context pre-execution review of EXP-101 (CF-LIQSWP-001/HYP-001) analysis implementation against the frozen EXP-100 AMENDMENT-14 TRAIN emission at git HEAD 8127c23. No EXP-100 modification, execution, rerun, or re-emission; no EXP-101 live execution; no TEST or holdout access. Reviewed git state was clean.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| **§1 Frozen source authority & gate-first** | `source.py:155-348` `validate_source_contract` | MATCHES | Family gate checked before any source rows; 264 cells verified; config_hash, event_log_sha256, NO_COST_CHARGED, one_backtest_node, nautilus-emission-v1, Nautilus=1.230.0 all validated. |
| **§1 TRAIN fence & UTC fence** | `source.py:112-126` `_validate_utc_fence`; `source.py:168` | MATCHES | `train_end_ns` (1_700_611_200 * 1_000_000_000) validated against `train_end_utc` "2023-11-22T00:00:00Z". |
| **§1 Composite ID uniqueness** | `source.py:129-152` `_validate_composite_uniqueness`; `source.py:319-337` | MATCHES | `(source_cell, raid_id)` uniqueness checked across all 264 cells. |
| **§1 Causal timestamp provenance** | `source.py:275-297` | MATCHES | `raid_ts_ns ≤ sweep_ts_ns ≤ return_ts_ns ≤ confirmation_ts_ns ≤ endpoint_ts_ns` validated per cell. |
| **§1 Schema/object/count reconciliation** | `source.py:234-268` | MATCHES | Required columns present; row counts match metadata; `source_configuration == config`; no rows after TRAIN fence. |
| **§1 Binding ATR_UNDEFINED exclusion** | `adapter.py:205-215` `_channel_frame` | MATCHES | `swing_atr` and `strong_move` exclude rows where `profile_undefined_reason == "ATR_UNDEFINED"`. |
| **§2 Mechanism & object identity** | `design.md:47-67`; `adapter.py:250` `cluster_ids=level_id` | MATCHES | Level-linked raid is measurement object; clustering by `level_id`; no orders/fills. |
| **§3 Configuration strata & fixed comparators** | `analysis.py:126-135` `contrasts`; `analysis.py:136-142` `stratum_columns` | MATCHES | 11 configs in 3 families; fixed comparators (PREVIOUS_1H, PREVIOUS_ASIA, ROLLING_7); strata exclude `config` so contrasts are within-stratum. |
| **§3 Population & censoring rules** | `adapter.py:205-215` `_channel_frame` | MATCHES | Primary population = COMPLETED & primary_attribution & primary_completed; failed/non-primary/censored/null/thin rows remain in census. |
| **§3 Primary estimators** | `analysis.py:126-135` `contrasts`; `adapter.py:127-130` `control_channels` | MATCHES | Mean `swing_atr`, mean `swing_duration_ns`, unpaired `strong_move` proportion difference. |
| **§4 Independent arm/comparator bootstrap** | `statistics.py:220-276` `clustered_contrast_bootstrap` `independent_arms=True` | MATCHES | Arm and comparator clusters resampled independently per design; `circular_cluster_indices` implements circular block bootstrap with `L_eff = min(max(1,L), n_clusters-1)`. |
| **§4 Block lengths L=2,5,10** | `statistics.py:336-354` `block_sensitivity`; `adapter.py:468-474` | MATCHES | Sensitivities computed for all three block lengths; L=5 is primary. |
| **§4 Empty arm handling** | `statistics.py:203-214` | MATCHES | Returns `EMPTY_ARM` reason with counts, null estimate/interval; row not removed. |
| **§4 Report layers (observed/ideal/interpretation)** | `adapter.py:489-502` | MATCHES | Output includes `observed`, `ideal`, `interpretation` fields; no machine value labels. |
| **§4 No prohibited value labels** | `adapter.py:489-502`; `contract.py:50-60` | MATCHES | No `SUPPORTED`, `WASH`, `CONTRADICTED`, `WORTH_EXPLORING`, `NOT_WORTH`, `INCONCLUSIVE` in output. |
| **§5 Cross-config destroy grouping** | `destroy.py:230-256` `stream_destroy_control` | MATCHES | Groups by `archive_symbol × timeframe × confirmation_method × confirmation_reference × side × status × primary_completed × 5-bit nullness class`; configuration pooled within group. |
| **§5 Derangement (zero fixed points)** | `destroy.py:72-85` `derange_indices`; `destroy.py:241-246` | MATCHES | Rejection sampling until `perm[i] != i` for all movable rows; singleton groups VOIDed. |
| **§5 Singleton VOID** | `destroy.py:237-246` | MATCHES | Groups with `n<2` produce `VOID_SINGLETON_GROUP`; rows not moved. |
| **§5 Destroy disclosure fields** | `adapter.py:397-419` control record evidence | PARTIAL | Includes raw contrast, destroyed draws, mean, interval, collapse_ratio, fixed_points, moved_rows, moved_eligible_values. Missing: empirical 95% destroyed interval for live (only fixture has it). |
| **§5 Exact nested 10k×2k destroy** | `destroy.py:507-532` `compute_exact_nested_destroy_se` | **MISSING** | Function is a placeholder (`pass`). Design requires: for each seed s=0..4, 10k bootstrap populations; for EVERY population b, recompute D_raw[s,b] AND all 2k deranged contrasts D_destroy[s,b,d]; compute m_destroy[s,b]; bootstrap_SE_raw[s]=std_b(D_raw); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy). Current implementation computes destroy contrasts only ONCE on original population, not per bootstrap population. |
| **§5 Fixture topology & plants** | `adapter.py:77-116` `make_fixture_frame` | DEVIATES | Design specifies explicit plants: swing_atr baseline 0.90/1.10 vs arm 1.40/1.60 (+0.50); duration baseline 3e12/4.2e12 vs arm 6.6e12/7.8e12 (+3.6e12 ns); strong_move baseline 1/4 vs arm 1/2 (+0.25). Shared fixture creates gradient values across 11 configs, not the two-arm explicit plants. |
| **§5 Nullness class: `duration_ns` vs `swing_duration_ns`** | `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns` | DEVIATES | Design §5 defines 5-bit nullness class as `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))`. Code uses `swing_duration_ns` (canonical). Byte-equal in practice but technically deviates from declared field name. |
| **§6 Sample size & complexity** | `design.md:164-177`; `adapter.py` | MATCHES | No minimum n; all rows retained; channels declared with sigma_denominator; 1 independent analysis module. |
| **§6 Hard/informative split** | `design.md:179-186`; `contract.py` `IntegrityStatus` | MATCHES | Hard blocks: gate-first, fence, causality, schema, no-local-accounting, deterministic, ATR exclusion, future-destroy validity, zero-cost. Informative: operator judges all effects. |
| **§7 Golden trace T1–T3** | `design.md:182-195`; EXP-100 `processor.py` | MATCHES | Hand-verified: independent PREVIOUS_1H/ROLLING_7 cells; inclusive return; primary attribution; swing_price=2.00, swing_atr=2.00, swing_bps=200, swing_duration_ns=3.6e12, strong_move=true. |
| **§8 Amendment ledger & final null** | `design.md:198-245` | MATCHES | 2L/3T/8N; no machine qualifier; no row hiding; F02/F04/F06 N/A; F07 satisfied. |
| **§9 Zero-cost disclosure** | `contract.py:10-25` `ZERO_COST_DISCLOSURE`; fixture output | MATCHES | Canonical text verbatim; `NO_COST_CHARGED`; no prohibited claims. |
| **Failed-control propagation** | `adapter.py:426-431` | MATCHES | Failed control reasons collected into overall integrity reasons; `VOID_FUTURE_DESTROY_SURVIVAL` blocks affected stratum/channel. |
| **Live orchestration & integrity gating** | `runtime.py:75-99` `_execute`; `analysis.py:233-238` | MATCHES | `--live` runs `run_live` → `adapter.integrity` → blocks `analyze` if integrity fails → atomic write. |

### Golden-trace diff

| Event | Expected from design | Implemented logic | Verdict |
|---|---|---|---|
| T1 — Separate PREVIOUS_1H/ROLLING_7 cells at 100.00 | Each starts own raid; excursion 1.20; count 0 | `processor.py:400-458` cell-local level/raid identity; side-aware excursion | MATCHES |
| T2 — Inclusive 100.00 return; expected-side 1H close | Return recorded; primary_attribution=true per cell | `processor.py:285-328,462-522` inclusive return; cell-local primary selection | MATCHES |
| T3 — Opposing endpoint at 98.00 | swing_price=2.00, swing_atr=2.00, swing_bps=200, duration=3.6e12 ns, strong_move=true | `processor.py:540-612` terminal arithmetic; duration alias implemented | MATCHES |
| Fixture plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion per design plants | Shared fixture uses gradient values across 11 configs | DEVIATES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation authorship in this context.
- **Gate-first:** PASS — `validate_source_contract` checks family gate (264 cells, `blocking_pass=true`) and all 264 per-cell gates before any parquet read.
- **TRAIN/holdout:** PASS — `train_end_ns` fence enforced; `VOID_AFTER_TRAIN` blocks any row beyond 2023-11-22T00:00:00Z; no TEST/holdout paths in code.
- **Registry:** PASS — `CF-LIQSWP-001/HYP-001` registered; 0 candidate slots; 0 counted TEST reads.
- **No Python backtest/local accounting:** PASS — `check_no_local_accounting` would pass; no accounting primitives; no strategy backtest in EXP-101.
- **One BacktestNode:** PASS — EXP-101 is analysis-only; EXP-100 metadata attests `one_backtest_node=true`.
- **Derangement:** PASS — `derange_indices` uses rejection sampling; `VOID_FIXED_POINTS` if any.
- **Zero cost:** PASS — Canonical disclosure verbatim; `NO_COST_CHARGED` in all metadata.
- **No research powering:** PASS — No MDE, power curves, `UNPOWERED`, detection floors. Only `INTEGRITY_Z=2.8` for validity.
- **PSR:** N/A — No trade/leg bps series.
- **Screen conversion/XENA:** N/A.
- **Battery rules:** PASS — No adaptive selection, capped read, exit selection, or phase-shift gate.

### Issues

1. **HIGH — Exact nested 10k×2k destroy not implemented.**
   **Design:** §5 "outer bootstrap: for each seed s=0..4, generate 10,000 cluster-bootstrap populations... For every population b, recompute the raw contrast D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]."
   **Code:** `destroy.py:507-532` `compute_exact_nested_destroy_se` is a placeholder (`pass`). `adapter.py:323-378` computes destroy contrasts only once on the original population, then bootstraps the *average* destroyed values. The design requires per-bootstrap-population destroy recomputation.
   **Required change:** Implement the exact nested destroy in `adapter.integrity` (or a called function): for each seed, for each of 10,000 bootstrap draws, resample clusters, then run all 2,000 derangements on that resampled population. Compute `m_destroy[s,b]` per draw, then `bootstrap_SE_mean_destroyed[s] = std_b(m_destroy[s,b])`.
   **Failing artifact:** `python/src/xen/liqswp_analysis/destroy.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

2. **HIGH — Fixture plants deviate from design specification.**
   **Design:** §5 FIXTURE-TOPOLOGY specifies 200 rows per arm (BASELINE/ARM) with explicit plants: swing_atr baseline 0.90/1.10 vs arm 1.40/1.60 (+0.50); duration baseline 3e12/4.2e12 vs arm 6.6e12/7.8e12 (+3.6e12 ns); strong_move baseline 1/4 vs arm 1/2 (+0.25).
   **Code:** `adapter.py:77-116` `make_fixture_frame` creates 200 rows × 11 configs with gradient values; no explicit two-arm plants.
   **Required change:** Either update the design to match the implemented multi-config fixture (with documented rationale), or implement a dedicated two-arm fixture matching the design's explicit plants for the pre-read smoke test.
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `quant-designer` (if design change) or `experiment-developer` (if implementation change).

3. **MEDIUM — Nullness class uses `swing_duration_ns` instead of declared `duration_ns`.**
   **Design:** §5 "nullness class is the five-bit tuple (is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias of swing_duration_ns."
   **Code:** `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns`; `adapter.py:132` inherits `CONTROL_NULL_COLUMNS = CHANNELS`.
   **Why it matters:** The design explicitly names `duration_ns` in the nullness class definition. While byte-equal in the frozen emission, the code should reference the declared alias name for traceability.
   **Required change:** Change `CONTROL_NULL_COLUMNS` to use `duration_ns` (or add both and verify equality), and update the 5-bit class computation accordingly.
   **Failing artifact:** `python/experiments/EXP-101/analysis_code/analysis.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

4. **MEDIUM — Missing `swing_price`/`swing_bps` source-field summaries in analysis output.**
   **Design:** §4 "Report counts, missingness, status/censor composition, mean, median, direct difference, interval, seed range, and every requested configuration. Raw `swing_price` and `swing_bps` are source-field summaries, not separate hard tripwire estimands."
   **Code:** `adapter.py:489-502` `analyze` method outputs medians for all channels but does not include raw mean/summary statistics for `swing_price` and `swing_bps` in the result rows.
   **Required change:** Add `swing_price` and `swing_bps` mean/median summaries to the analysis output (can be in `observed` or as separate fields).
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

5. **LOW — Empirical 95% destroyed interval missing from live control disclosure.**
   **Design:** §5 "disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical 95% interval; collapse_fraction..."
   **Code:** `adapter.py:397-419` fixture control records include `destroyed_interval` (from `future_destroy_attestation`), but live control path uses `destroyed_outer_se` (hypot combination) and does not compute the empirical quantile interval from the 2,000 destroyed contrasts.
   **Required change:** Ensure live control records include the empirical 95% interval from the 2,000 destroyed contrasts (not just the bootstrap SE interval).
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

### Summary

**REVISE.** The EXP-101 analysis implementation correctly implements the majority of the design: frozen source validation, independent arm/comparator bootstrap, derangement-based cross-configuration destroy, singleton VOID, UTC fence + composite ID, failed-control propagation, live orchestration with integrity gating, and neutral report layers. The golden trace matches the frozen EXP-100 logic.

Two **HIGH** issues block execution readiness:
1. The exact nested 10k×2k destroy (per-bootstrap-population destroy recomputation) is not implemented — the current code computes destroy contrasts only once on the original population.
2. The fixture plants do not match the design's explicit two-arm plant specification.

Three **MEDIUM/LOW** issues should be addressed before execution:
3. Nullness class field name mismatch (`duration_ns` vs `swing_duration_ns`).
4. Missing `swing_price`/`swing_bps` source-field summaries in output.
5. Live control disclosure missing empirical 95% destroyed interval.

Route to `experiment-developer` for implementation fixes (issues 1, 3, 4, 5) and `quant-designer` for design/implementation alignment on fixture plants (issue 2).


## QA run 11 — 2026-08-17T23:50:59Z — mode: subagent — HEAD 62983d0cf0136b7caf1ec2aea8c41d3b92abdec1

Verdict: **REVISE**

Scope: fresh-context verification that the run-10 REVISE findings at HEAD 8127c23 are correctly resolved in the e57847c working tree (HEAD 62983d0; tree clean; later commits touch only skill/QA docs). Reviewed state: `git rev-parse HEAD` = 62983d0cf0136b7caf1ec2aea8c41d3b92abdec1, `git status --short` = clean. Read-only review; no file modified except this append-only record. Design text was read first; code was verified independently of the developer's summary.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1 FROZEN-SOURCE gate-first authority | `source.py:155-176` `validate_source_contract` | MATCHES | Family gate (`EXP-100/results/estimand_validation.json`, blocking_pass=true, n_cells=264 verified on disk) checked before any parquet read; per-cell gates all checked (`VOID_CELL_GATE` source.py:208). |
| §1 TRAIN fence & UTC fence | `source.py:113-127` `_validate_utc_fence`; `source.py:168`; `adapter.py:28-29` `TRAIN_END_NS`/`TRAIN_END_UTC` | MATCHES | 1_700_611_200e9 == 2023-11-22T00:00:00Z (re-derived by ISO parse; string carries "Z" so the aware-datetime path is taken); fence files PINNED with matching train_end_utc (all 264); endpoint scan filters rows <= train_end. |
| §1 Seal: config_hash / event_log_sha256 / cost_model | `source.py:222-230` | MATCHES | config_hash vs gate attestation, event log SHA256 vs metadata, cost_model=NO_COST_CHARGED all enforced fail-closed. |
| §1 Seal: emission_contract_version / Nautilus / one_backtest_node / manifest SHA256 | `source.py:155-340` | **DEVIATES** | None of these §1 "seal/require" fields are validated. All 264 `run_metadata.json` carry emission_contract_version=nautilus-emission-v1, nautilus_version=1.230.0, one_backtest_node=true (verified on disk), and fence manifest_sha256 matches the design text — but the check is absent, so the hard seal is fail-open for these fields. See Issue 1. |
| §1 Composite (source_cell, raid_id) uniqueness | `source.py:130-153`, `source.py:330-337` | MATCHES | Eager per-cell composite key check (run-10 f-item). |
| §1 Within-cell object-id duplicate detection | `source.py:306-316` | MATCHES | Cell-scoped group-by on raid_id with explicit cell-scope comment (run-10 f-item). |
| §1 Causal timestamp provenance | `source.py:286-303` | MATCHES | raid<=sweep<=return<=confirmation<=endpoint per cell; `VOID_CAUSAL_ORDER`. |
| §1 Binding ATR_UNDEFINED exclusion | `adapter.py:262-270` `_channel_frame` | MATCHES | swing_atr/strong_move exclude ATR_UNDEFINED rows; excluded count reported in census (`adapter.py:595`). |
| §3 Strata, 11 configs, fixed comparators | `analysis.py:127-143` | MATCHES | 8 (arm, comparator) contrasts with fixed comparators PREVIOUS_1H / PREVIOUS_ASIA / ROLLING_7; stratum key is the 5-tuple, config pooled within stratum (configuration pooling per §3/§5). |
| §3 Population & censoring | `adapter.py:262-270` | MATCHES | Outcome population = COMPLETED & primary_attribution & primary_completed; failures stay in census; swing_price/bps finite-only. |
| §3 Primary estimators | `adapter.py:180-186`; `statistics.py:37-60` | MATCHES | Mean swing_atr, mean swing_duration_ns, unpaired strong_move proportion difference; time is reported in hours in live output per design. |
| §4 §7 Independent arm/comparator bootstrap | `statistics.py:120-243`; `analysis.py:147` `independent_arms=True` | MATCHES | Arm and comparator clusters resampled independently; `L_eff=min(max(1,L), n_clusters-1)`; circular blocks; single-cluster annotated `ONE_CLUSTER` (not silently treated as valid). |
| §4 Block lengths 2/5/10; L=5 primary | `statistics.py:336-354`; `adapter.py:489-493` | MATCHES | `observed_L2/L5/L10` all emitted; nested outer bootstrap uses block_length=5 (`nested_block_length`, adapter.py:199). |
| §4 Empty-arm handling | `statistics.py:46-53`; `destroy.py:845-862` | MATCHES | Counts + EMPTY_ARM_OR_COMPARATOR reason + null interval; row retained; integrity passes with a disclosed "no estimate possible" note (design §4 "do not remove the row or infer a direction"). |
| §4 Report layers / no value labels | `adapter.py:555-560` | MATCHES | observed/ideal/interpretation fields; no SUPPORTED/WASH/CONTRADICTED/etc. machine labels. |
| §5 CONTROL grouping (8-tuple + 5-bit nullness, config pooled) | `analysis.py:41-50`, `adapter.py:26-43`; `destroy.py:196-210` | MATCHES | Group = (archive_symbol, timeframe, confirmation_method, confirmation_reference, side, status, primary_completed) × 5-bit nullness; **nullness uses declared `duration_ns` alias** (run-10 issue 3 closed); alias byte-equality asserted in `adapter.py:338-352` (`VOID_DURATION_ALIAS_NULLNESS_MISMATCH`, `VOID_DURATION_ALIAS`). |
| §5 Derangement (zero fixed points) | `destroy.py:87-95` `derange_indices` | MATCHES | Rejection sampling until no fixed points; mappings assert fixed_points=0; brute-force test coverage (`test_destroy.py:258`). |
| §5 Singleton groups (n<2) | `destroy.py:236`, `destroy.py:371` | MATCHES (label note) | Rows stay fixed, control voided and disclosed, but the emitted label is `VOID_SINGLETON_GROUP` whereas the design names it `VOID_NO_DERANGEMENT`. Same semantics; label not aligned. See Issue 3. |
| §5 Exact nested 10k×2k outer bootstrap | `destroy.py:520-747` `nested_destroy_bootstrap`; `destroy.py:750-816` `_destroy_draw` | MATCHES | **run-10 issue 1 closed.** For each seed s, 10,000 cluster populations via §4 mechanics (independent arms for EXP-101); RAW and the full 2,000-destroy statistic recomputed inside EVERY population b from per-cluster/per-group sufficient statistics (group aggregates re-derived on b's rows, so the donor pool follows the resample). Closed form `m_destroy[b]=Σ_g(W_gG_g−S_g)/(m_g−1)` for m_g≥2 (else S_g) verified against the design's literal draw-recompute procedure by an independent numeric probe (std_b(raw) and std_b(m_destroy) agreement); `bootstrap_SE_raw[s]=std_b(D_raw,ddof=1)`; `bootstrap_SE_mean_destroyed[s]=sqrt(var_between + mean_b(Var_draw)/n_destroy)` computed and disclosed per seed. Docstring and code match. |
| §5 AMENDMENT-15 live read inequality | `destroy.py:818-939` `future_destroy_attestation` | MATCHES | If `abs(D_raw) > INTEGRITY_Z*bootstrap_SE_raw[s]` then `abs(m_destroy) > INTEGRITY_Z*bootstrap_SE_raw[s]` => survival seed => `VOID_FUTURE_DESTROY_SURVIVAL` (destroyed mean compared against the RAW bootstrap SE, not `bootstrap_SE_mean_destroyed`); threshold string in evidence is "INTEGRITY_Z * bootstrap_SE_raw[s]"; nested SE still disclosed per seed (requirement (a),(b) met). Non-finite raw / missing destroyed statistic => VOID reasons (invalidity, never null-result); collapse_ratio NaN when D_raw zero/non-finite; no raw-bite seeds => control reported without collapse claim (requirement (c) met). |
| §5 INTEGRITY_Z=2.8 validity-only | `destroy.py:49` | MATCHES | Only power-unrelated scale constant; no MDE/power/detection-floor code anywhere. |
| §5 Fixture topology & plants | `adapter.py:92-170` `make_fixture_frame`; `analysis.py:150-154` | MATCHES (note) | **run-10 issue 2 closed.** Two-arm explicit plants per pair: swing_atr 0.90/1.10 vs 1.40/1.60 (+0.50); duration 3e12/4.2e12 vs 6.6e12/7.8e12 (+3.6e12 ns); strong_move at 1/4 vs 1/2 (+0.25); 200 rows/arm; permutation seed 4; timestamp base/step per design; receipt raw_estimates = exactly +0.5 / +3.6e12 / +0.25 for every contrast. Shared baseline labels reuse `FIXTURE-{label}-level-{i:04d}` across pair blocks => 3-row clusters (topology says cluster_size=1); statistically inert (identical rows). See Issue 2. |
| §6 Complexity/no-power/no-veto | `design.md:167-187`; analysis code | MATCHES | No MDE/power curve/detection floor/`UNPOWERED`/`min_powered_seeds`/`n_legs_floor`; PSR N/A (no trade/leg-bps series); no cost function in live path. |
| §7 Golden trace T1–T3 | `processor.py:286-330` (inclusive return), `462-522` (primary attribution), `555-612` (terminal swing arithmetic, duration_ns alias) | MATCHES | Hand-verified below. |
| §8 Amendment ledger | `design.md:198-263` | MATCHES | 14 amendments; running counts re-derived and consistent; AMENDMENT-15 DIRECTION: LOOSER, final tally exactly 3 looser / 3 tighter / 8 neutral; no ≥3 one-directional streak (max 2); final null selection accounting consistent. |
| §9 / ZERO-COST disclosure | `contract.py:10-27`; `test_contract.py:33` | MATCHES | Canonical text verbatim (test asserts byte equality); emitted in every receipt; NO_COST_CHARGED confirmed in all 264 source metadata cells. |
| Fixture control gating / receipt | `runtime.py:24-61`; `fixture_integrity.json` | MATCHES | **run-10 issue 5 closed / receipt regenerated** (committed in e57847c): 24/24 control records `blocking_pass=true`, `destroyed_interval` (empirical 95%, np.quantile 0.025/0.975) present on every record, nested seeds disclosed per seed with both SEs, raw_bite seeds listed, zero survived seeds anywhere. |
| swing_price/swing_bps source-field summaries | `adapter.py:515-549`, `adapter.py:560` | MATCHES | **run-10 issue 4 closed** — `source_field_summaries` with arm/comparator n, non_null, mean, median for both channels in every value row. |

### Golden-trace diff

| Event | Expected (from design §7) | Implemented logic (hand-verified) | Verdict |
|---|---|---|---|
| T1 — separate PREVIOUS_1H / ROLLING_7 cells, level high 100.00, bar 101.20/100.80/101.00, raid_atr=1.00 | Each cell starts its own raid, prior_raid_count=0, max_excursion=1.20, null return, no cross-cell ordering | `processor.py` is cell-local (per-cell processor/state); excursion 101.20−100.00=1.20; strictly-beyond start on the completed observation bar; return recorded if same bar returns (`processor.py:303-325`, AMENDMENT-13 keeps raid live) | MATCHES |
| T2 — completed observation low=100.00 returns; 11:00 expected-side 1H close assigns primary_attribution=true per cell; equal-price cross-config level does not demote | Inclusive `bar.low <= price` return; primary=max(expected, (sweep_ts, raid_id)); equal-price level in another configuration cannot CONFIRMED_NON_PRIMARY this raid (cell-local identity) | `processor.py:303-315`, `processor.py:480-520` | MATCHES |
| T3 — 12:00 opposing reference event ends primary swing; level=100.00, raid_atr=1.00, swing_extreme=98.00 | swing_price=2.00, swing_atr=2.00 (2.00/1.00), swing_bps=200 (2.00/100×10⁴), swing_duration_ns=duration_ns=3.6e12 (12:00−11:00), strong_move=true (2.00>1.20) | `processor.py:555-612`: swing_price=level−swing_extreme (HIGH), swing_atr=swing_price/raid_atr, swing_bps=(swing_price/level_price)×10_000, strong_move=swing_atr>max_excursion_atr (2.00>1.20), swing_duration_ns=endpoint−confirmation, duration_ns=swing_duration_ns (alias, line 612) | MATCHES |
| Fixture plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion, destroyed means inside the raw bite band per seed | Receipt raw_estimates exactly 0.5 / 3.6e12 / 0.25 for all 24 controls; destroyed means ~0.0002–0.0004 ≪ 2.8·SE_raw; survived seeds [] everywhere | MATCHES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation authorship in this context.
- **Gate-first & per-cell gates:** PASS — family gate and all 264 cell gates blocking before any row read.
- **TRAIN/holdout fence:** PASS — `VOID_AFTER_TRAIN` plus scan-time endpoint filter ≤ 2023-11-22T00:00:00Z; no TEST/holdout path in the analysis.
- **Registry preconditions:** PASS — CF-LIQSWP-001 REGISTERED (docs/signal-registry/candidate-families/cf-liqswp-001.md), HYP-001 registered with EXP-101; EXP-100/HYP-000 AMENDMENT-14 COMPLETED, 0 counted TEST reads / 0 holdout reads / 0 candidate slots.
- **No local accounting / no backtest:** PASS — `check_no_local_accounting("experiments/EXP-101")` → `{'ok': True, 'banned_defs_found': []}`; EXP-101 runs only fixture/live analysis entry points (no BacktestNode).
- **One BacktestNode:** PASS for EXP-101 (analysis-only); EXP-100 metadata attests `one_backtest_node=true` in all 264 cells (source metadata verified; the analysis does not itself reconstruct a node).
- **Derangement destroy:** PASS — `derange_indices` rejection sampling (zero fixed points); `build_destroy_mappings`/draw path assert fixed_points=0; brute-force parity test green.
- **Zero cost:** PASS — disclosure verbatim; NO_COST_CHARGED in all source metadata; no cost/scoped legacy cost-model imports in the live path.
- **No research powering:** PASS — no MDE/power/floor terms found; only INTEGRITY_Z=2.8 validity.
- **PSR / screen conversion / XENA:** N/A — no trade/leg-bps series, no SPDR-cited money effects, no XENA routing.
- **Amendment direction ledger:** PASS — final 3 looser / 3 tighter / 8 neutral; no ≥3 streak requiring an operator flag.

### Issues

1. **MEDIUM — §1 seal attestations not validated by the source contract (NEW, pre-existing).**
   **Design:** §1 `seal` — "require emission_contract_version=nautilus-emission-v1, Nautilus=1.230.0, cost_model=NO_COST_CHARGED, and one_backtest_node=true"; §1 fence — "manifest SHA256 4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0".
   **Code:** `source.py:155-340` `validate_source_contract` validates config_hash, event_log_sha256, cost_model, fence status/UTC, counts, schema, causality, composite uniqueness — but never reads or checks `emission_contract_version`, `nautilus_version`, `one_backtest_node`, or the fence `manifest_sha256` (verified by grep: no such identifiers in `python/src/xen/liqswp_analysis`). The data currently attests all of these correctly (264/264 metadata + fence hashes match the design), so this is unenforced enforcement rather than an active violation — but prior QA run 10's trace claimed these fields were "all validated", which is inaccurate. The hard-block seal is fail-open for these fields.
   **Required change:** In `validate_source_contract` (source.py), read `run_metadata.json` for `emission_contract_version == "nautilus-emission-v1"`, `nautilus_version == "1.230.0"`, `one_backtest_node == true`, and the fence `manifest_sha256 == "4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0"`, appending VOID reasons on any mismatch; alternatively record an operator-approved deviation to the §1 seal. Route: `experiment-developer`.

2. **LOW — Fixture shared baseline labels reuse level_ids across pair blocks.**
   **Design:** §5 FIXTURE-TOPOLOGY — "level_id=FIXTURE-{arm}-level-{i:04d}; cluster_size=1; one row is one complete level cluster".
   **Code:** `adapter.py:128` — `level_id = f"FIXTURE-{label}-level-{index:04d}"` using the label only; PREVIOUS_1H (3 pairs), PREVIOUS_ASIA (2), ROLLING_7 (3) each reuse the same 200 level_ids across their pair blocks, so those "clusters" hold 2–3 rows instead of 1. Affects nothing statistically (rows within a reused cluster are identical values and identical timestamps, so bootstrap moments match cluster_size=1) and the bite passes on every control, but the literal topology statement is not met.
   **Required change (optional):** scope the level_id by pair block (e.g., `FIXTURE-{arm}-{pair}-level-{i:04d}`) to make every cluster exactly one row, then regenerate the fixture receipt. Route: `experiment-developer`.

3. **LOW — Destroy VOID label differs from design term.**
   **Design:** §5 — "A group with n<2 produces VOID_NO_DERANGEMENT for that control population and remains disclosed."
   **Code:** `destroy.py:236,371` emit `VOID_SINGLETON_GROUP` (and `VOID_NO_MOVABLE_ROWS` when no group is movable). Behaviour identical (rows fixed, population void, disclosed); only the machine label differs.
   **Required change (optional):** rename the reason to the registered label `VOID_NO_DERANGEMENT`, and note the near-null `m_g==1` nested-arm path (`destroy.py:800-802`, rows stay fixed and contribute S_g) is consistent with the same rule.

Non-issue note (recorded for the operator): at the smoke scale (10 outer replicates), the strong_move raw bite fires on seeds 0 and 4 only (per-seed SEs 0.074–0.151 inflated by 10-draw sampling); under AMENDMENT-15's seed-conditional live-read the control still passes (destroyed mean 0.00024 ≪ 2.8·SE_raw on every biting seed, no destroyed survival). At live scale (10,000 replicates) the strong_move SE tightens to ≈0.04 and every seed bites, so the design's "every seed and channel must satisfy the raw-bite" fixture clause is fully exercised on live settings.

### Prior run-10 findings — verification result

All five run-10 REVISE items are verified RESOLVED in the e57847c state: (1) exact nested 10k×2k destroy implemented and numerically verified, (2) registered two-arm fixture plants implemented with exact raw contrasts, (3) nullness class uses the `duration_ns` alias with asserted byte-equality, (4) swing_price/swing_bps source-field summaries emitted, (5) empirical 95% destroyed interval present in live control evidence; source.py repairs (composite uniqueness, UTC fence, within-cell duplicate detection) and the regenerated, all-passing `fixture_integrity.json` receipts are confirmed. No functional regression found in the resolved areas.

## QA run 12 — 2026-08-20T19:40:49Z — mode: subagent — HEAD 0f08bd13a68393be9d1f8344b69af6c6cff79f7b
Verdict: APPROVE

Scope: fresh-context, analysis-only re-read of the frozen EXP-100 AMENDMENT-14 TRAIN emission (264 cells) against the current EXP-101 design through AMENDMENT-16. No new engine, TEST, holdout, or EXP-100 rerun. Design text was read first; code was verified independently of prior QA. Unofficial `analysis_results.json` was not read. Dirty/untracked paths present and ignored: `.jspace/`, `docs/superpowers/plans/2026-08-20-exp-101-104-handoff.md`, `python/experiments/EXP-10{1,2,3,4}/results/analysis_results.json`.

Prior run-11 (17 Aug, REVISE) resolution:
| Run-11 issue | Current verdict | Evidence |
|---|---|---|
| §1 seal fields not checked | **RESOLVED** | `source.py:16-22,221-238` fail-closed on `emission_contract_version`, `nautilus_version`, `one_backtest_node`, `manifest_sha256`; tests in `test_source.py:151-170` |
| Fixture shared baseline `level_id` reuse | **PERSISTS (info)** | `adapter.py:128` still `FIXTURE-{label}-level-{index:04d}`; plants and bite still exact (see Notes) |
| `VOID_SINGLETON_GROUP` vs `VOID_NO_DERANGEMENT` | **SUPERSEDED** | AMENDMENT-16 (operator-approved 2026-08-18): n<2 groups stay fixed and do not void; code emits only `VOID_NO_MOVABLE_ROWS` / `VOID_NO_CHANGED_VALUE` |

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1 Frozen AMENDMENT-14 TRAIN source; 264-cell gate-first; no EXP-100 rerun | `source.py:155-176`; `adapter.py:354-363`; `analysis.py:194-201`; EXP-100 `estimand_validation.json` `blocking_pass=true`, `n_cells=264` | MATCHES | Live path validates the family gate and per-cell gates before parquet collect; root is `data/nautilus_runs/EXP-100/full` |
| §1 Seal: contract v1, Nautilus 1.230.0, `NO_COST_CHARGED`, one node, manifest SHA256 `4cdc7b01…1de0` | `source.py:16-22,191-196,221-238` | MATCHES | Run-11 gap closed. Fail-closed VOID reasons for each seal field; manifest start/pin also checked |
| §1 TRAIN fence 2021-06-02T00:01:00Z–2023-11-22T00:00:00Z; no holdout | `source.py:23-28,112-126,197-218,247-266`; `adapter.py:31-32`; `scan_train_columns` | MATCHES | Endpoint filter `<= train_end_ns`; `VOID_AFTER_TRAIN` / `VOID_BEFORE_TRAIN_START`; no TEST/holdout path |
| §1 Identity: `config`==`source_configuration`; metadata↔row; composite `(cell, raid_id)` | `source.py:112-119,239-246,306-337` | MATCHES | Timeframe identity is `f"{observation_minutes}m"` (60-minute cells → `60m`, not `1h`) |
| §1 Duration alias; `pre_mfe_retrace` out of HYP-001 | `adapter.py:40-48,438-454`; CHANNELS omit `pre_mfe_retrace` | MATCHES | Byte-equal `duration_ns`/`swing_duration_ns` asserted (`VOID_DURATION_ALIAS*`). Hours display is a later report conversion, not the estimand unit (Note 2) |
| §1 Binding ATR_UNDEFINED exclusion | `adapter.py:365-375`; `analysis.py:70-77` | MATCHES | `swing_atr` / `strong_move` drop `ATR_UNDEFINED`; other channels and census keep the rows; excluded count in census |
| §2 Mechanism / object identity: level-linked raid vs later swing; cluster by `level_id` | `adapter.py:387-416`; `statistics.py:38-81` | MATCHES | No orders/fills/P&L; clusters are complete `level_id` histories sorted by `(min(sweep_ts_ns), level_id)` |
| §3 11 configs; fixed comparators PREVIOUS_1H / PREVIOUS_ASIA / ROLLING_7 | `analysis.py:79-88` | MATCHES | Eight (arm, comparator) pairs only; no adaptive arm |
| §3 Result rows by symbol×TF×method×reference×side×config; **stratum key omits config** so both arms share a partition | `analysis.py:89-95`; `adapter.py:437` `_strata` | MATCHES | Override drops base `config` stratum. Fixture value-row `stratum` is the 5-tuple. If config were in the key, arm and comparator would split and every contrast would be empty |
| §3 Outcome population COMPLETED ∧ primary_attribution ∧ primary_completed; finite price/bps/duration | `adapter.py:365-375`; `statistics.py:47-51` | MATCHES | Census retains failed/non-primary/censored/null/thin |
| §3 Primary estimators: arm−comparator mean `swing_atr`, mean `swing_duration_ns`; unpaired `strong_move` proportion | `statistics.py:38-81`; `adapter.py:180-186` | MATCHES | Boolean mean is the unpaired proportion; medians are secondary; `swing_price`/`swing_bps` are summaries (`adapter.py:271-298`) not tripwire channels |
| §4 Independent arm/comparator cluster resampling; `L_eff=min(max(1,L), n_clusters-1)`; 10k draws; seeds 0–4; NumPy linear quantile; L=5 + L=2/10 | `analysis.py:99` `independent_arms=True`; `statistics.py:84-97,113-147,220-276,318-399`; `adapter.py:199,468-474` | MATCHES | Distinct configuration populations resampled separately. Empty arm → `EMPTY_ARM_OR_COMPARATOR` with counts, null interval, row kept. One cluster → `ONE_CLUSTER`, not a silent SE |
| §4 Report layers; no machine value labels | `adapter.py:489-502,691-704`; `contract.py:50-60`; `runtime.py:75-99` | MATCHES | `observed`/`ideal`/`interpretation`; prohibited names absent |
| §5 Destroy grouping: 7-tuple + 5-bit nullness; **config pooled**; sort note | `analysis.py:40-55`; `destroy.py:196-210,355-368` | MATCHES | Nullness uses declared `duration_ns`. Fixture control `group_sizes=[3200]` = all 11 configs in one group. Groups follow frame encounter order rather than an explicit `(raid_id, original_row_position)` sort (Note 3); still a uniform derangement |
| §5 Derangement; AMENDMENT-16 singletons stay fixed; void only `VOID_NO_MOVABLE_ROWS` / `VOID_NO_CHANGED_VALUE` | `destroy.py:156-163,237-259,277-278,401-411,450-451`; `test_destroy.py:110-150` | MATCHES | n<2 rows unmapped and listed in `group_sizes`; they do not void. All-singleton → `VOID_NO_MOVABLE_ROWS`; unchanged values → `VOID_NO_CHANGED_VALUE`. No `VOID_SINGLETON_GROUP` on the live path |
| §5 Live destroy on unresampled donor (all configs in stratum); 2,000 draws `default_rng(d)` | `adapter.py:186-214,447-478`; `destroy.py:318-468` | MATCHES | Donor = `_channel_frame` (config-pooled); contrast evaluated on arm/comparator labels. All 2,000 destroyed contrasts disclosed (`destroyed_draws: 2000` plus the vector) |
| §5 Nested 10k×2k using §4 mechanics; `bootstrap_SE_raw` / `bootstrap_SE_mean_destroyed` disclosed | `destroy.py:599-816`; independent branch `759-791` | MATCHES | Closed-form per-population destroy mean; nested SE disclosed with between + within/n_destroy. Under AMENDMENT-15 the bite does not use the nested SE |
| §5 AMENDMENT-15 live read: if `abs(D_raw) > 2.8×SE_raw[s]` then require `abs(m_destroy) ≤ 2.8×SE_raw[s]` | `destroy.py:49,949-1105` | MATCHES | Threshold string `INTEGRITY_Z * bootstrap_se_raw[s]`; survival → `VOID_FUTURE_DESTROY_SURVIVAL`. No raw bite → control reported, no collapse claim. Empty arm disclosed, not failed |
| §5 Fixture topology and plants | `adapter.py:49-52,92-170`; `analysis.py:150-154`; `runtime.py:101-107`; `fixture_integrity.json` | MATCHES (note) | 200 rows/arm/pair; plants +0.50 ATR / +3.6e12 ns / +0.25; seed-4 permutation; `raid_id=fixture-raid-{pos:04d}`; fixture `n_boot=10`, live 10,000. Shared comparator `level_id`s yield 3-row clusters for PREVIOUS_1H/ASIA/ROLLING_7 (Note 1); raw estimates remain exact |
| §6 HARD/INFORMATIVE; no MDE/power/PSR; complexity | `design.md` §6; `liqswp_analysis/` (no MDE/`UNPOWERED`/cost imports) | MATCHES | PSR N/A (no trade/leg series). `INTEGRITY_Z=2.8` validity-only |
| §7 Golden trace T1–T3 (frozen engine; no re-emit) | `processor.py:286-330,400-458,462-522,540-612` | MATCHES | See golden-trace table. Observation hour cells emit `f"{observation_minutes}m"` → `60m` (`processor.py:601`) |
| §8 Amendment ledger through AMENDMENT-16 | `design.md` §8; checkpoint `design.md:121-140` | MATCHES | 4 looser / 3 tighter / 8 neutral; A15+A16 looser streak = 2 (<3). No machine qualifier; F02/F04/F06 N/A; F07 retain every row |
| §9 Zero-cost verbatim | `contract.py:10-27`; `test_contract.py:33`; fixture `zero_cost_disclosure` | MATCHES | Canonical text; no live cost function; no `evaluation_cost_legacy` / `spread_scale` / `bybit_round_trip` on this path |
| Live one-hour observation label `60m` not `1h` | `processor.py:601`; `source.py:113-116` | MATCHES | Identity check reconstructs timeframe as `{observation_minutes}m`. Confirmation reference stays `1H` |

### Golden-trace diff

| Event | Expected from design | Implemented logic | Verdict |
|---|---|---|---|
| T1 — separate PREVIOUS_1H / ROLLING_7 cells; level 100.00; bar 101.20/100.80/101.00; `raid_atr=1.00` | Each cell starts its own raid; `prior_raid_count=0`; `max_excursion=1.20`; null return; no cross-cell ordering | Cell-local processor; HIGH start on `high>100`; T1 `low=100.80` does not return; excursion 101.20−100.00=1.20 (`processor.py:286-330,400-458`) | MATCHES |
| T2 — 10:15/11:00 return and expected-side 1H close | Inclusive `low<=100` records return; AMENDMENT-13 keeps raid live; 11:00 expected-side close sets `primary_attribution=true` per cell; equal-price other config does not demote | Inclusive return (`processor.py:303-315`); cell-local primary = latest expected (`processor.py:480-520`) | MATCHES |
| T3 — 12:00 opposing endpoint; extreme 98.00 | `swing_price=2.00`, `swing_atr=2.00`, `swing_bps=200.0`, `swing_duration_ns=duration_ns=3.6e12`, `strong_move=true` (2.00>1.20) | HIGH `level−extreme`; ATR and bps arithmetic; duration = endpoint−confirmation; alias `duration_ns` (`processor.py:555-612`) | MATCHES |
| Observation hour cell label | Live 60-minute observation cells labelled `60m`, not `1h` | `timeframe = f"{observation_minutes}m"` | MATCHES (golden-trace prose still says “15m/1H source cells”; that is confirmation/wording, not the parquet label) |
| Fixture plants | +0.50 / +3.6e12 ns / +0.25; destroyed mean inside raw bite band; 2,000 derangements, 0 fixed points | Receipt `raw_estimate` 0.5 / 3600000000000.0 / 0.25; `destroyed_mean` ~4e-4; `destroyed_survives_seeds=[]`; `fixed_points=0`; `group_sizes=[3200]`; `population_match=true`; threshold is raw SE | MATCHES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; this conversation did not implement the code.
- **Gate-first / 264 cells:** PASS — EXP-100 `estimand_validation.json` `blocking_pass=true`, `n_cells=264`; live validator requires the same before row collect.
- **TRAIN / holdout:** PASS — pinned INFR-021 TRAIN window only; no TEST/holdout query in the analysis path.
- **Registry:** PASS — `CF-LIQSWP-001` REGISTERED; HYP-001 → EXP-101; vehicle is TRAIN re-analysis, not a counted TEST read.
- **No Python price backtest / no local accounting:** PASS by inspection — EXP-101 has `analysis_code/` only (no `code/` runner). No accounting primitives in `analysis.py` or `xen.liqswp_analysis`. `check_no_local_accounting` was not executed this run (read-only; no shell).
- **One BacktestNode:** PASS — analysis-only; no new `BacktestNode`. Seal still requires source `one_backtest_node=true`.
- **Derangement (L-28):** PASS — rejection sampling, zero fixed points.
- **AMENDMENT-15 / 16 (binding, not relitigated):** PASS — destroyed non-bite uses raw SE; singletons stay fixed and disclosed; void only no-movable / no-changed-value.
- **Zero cost:** PASS — verbatim disclosure; no live cost call; no cost directive.
- **Powering strip / PSR:** PASS / N/A — no MDE, detection floor, `UNPOWERED`, or trade/leg series.
- **Screen conversion / XENA:** N/A.
- **Battery §13:** PASS as declared — no battery selection, capped read, or path-dependent exit gate.
- **Amendment streak:** PASS — no ≥3 one-directional streak.
- **Mandatory design blocks:** PASS — MECHANISM, OBJECT-IDENTITY, CONTROL, TRIPWIRE, operator-only bands, SAMPLE-SIZE, GOLDEN-TRACE, HARD/INFORMATIVE, ZERO-COST, amendment ledger. CONVERSION-PIN / COST-DIRECTIVE N/A.

### Issues

No blocking issues.

1. **INFO — Fixture comparator `level_id`s are reused across pair blocks.** Design §5 `cluster_size=1`; `adapter.py:128` keys `level_id` by label only, so PREVIOUS_1H / PREVIOUS_ASIA / ROLLING_7 clusters hold 2–3 identical rows. Means and planted contrasts stay exact (`raw_estimate` 0.5 / 3.6e12 / 0.25). Optional: scope `level_id` by pair if a literal one-row cluster receipt is wanted.
2. **INFO — Duration remains nanoseconds in the machine artifact.** Design §1 asks hours as `swing_duration_ns / 3_600_000_000_000` for display. The registered estimand is still mean `swing_duration_ns`. Convert at analysis.md time; do not change the estimator.
3. **INFO — Destroy groups are not re-sorted by `(raid_id, original_row_position)`.** `destroy.py:196-210,355-368` uses encounter order. The mapping is still a uniform zero-fixed-point derangement of the declared groups.

Supervisor may run (not run here): `PYTHONPATH=python/src python -m pytest -q python/tests/liqswp_analysis python/tests/test_exp101_analysis_live.py`; `check_no_local_accounting("python/experiments/EXP-101")`.
