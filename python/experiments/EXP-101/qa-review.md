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
