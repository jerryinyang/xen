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

