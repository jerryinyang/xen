## QA run 1 — 2026-08-11T03:52:39Z — mode: subagent — HEAD d9730b5982c8d4b4e2ed76f2f458d87e2ee70a03

Verdict: REVISE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Liquidity-level catalogue includes previous 1D/1W/4H/1H levels | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:6,56`; checkpoint `design.md:104` | DEVIATES | Checkpoint excludes 1W. |
| Sweep causal ordering and raid state | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:10-22`; checkpoint `design.md:131-153` | MATCHES | Strict excursion, inclusive return, ambiguity, ordering, and positive reversal are stated. |
| Value-gap interval and profile definition | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:43-49,67`; checkpoint `design.md:158-181` | MATCHES | Includes the strict rule `gap_span < 0.30*(VAH-VAL)`. |
| Timeframes, confirmation references, sessions, ATR, 1m input, fences and holdout | checkpoint `design.md:75-121,141-153,305-307` | MATCHES | 1H references are used for 15m/30m and 1D for 1h. |
| Controls and required emissions | checkpoint `design.md:204-253`; EXP-102 `design.md:46-55` | MATCHES | Design-only review; no implementation exists. |

### Golden-trace diff

No implementation or smoke emission exists. The design-only golden trace is consistent for the matched clauses; the 1W catalogue branch is an explicit deviation.

### Governance & boundary

- Review mode: fresh `subagent` context.
- No experiment was run and no implementation was reviewed.
- Reviewed state: 5 modified files and 11 untracked paths at the reviewer timestamp.
- Literal 100% SoT preservation is not established.

### Issues

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 2 — 2026-08-13T18:17:52Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75
Verdict: REVISE

Review scope: current `python/experiments/EXP-102/design.md` against checkpoint
`2026-08-11-019-liquidity-sweeps`, the registered `CF-LIQSWP-001/HYP-002` family
contract, and the shared pipeline/governance rules. This is a frozen analysis
readiness review of the existing EXP-100 AMENDMENT-13 TRAIN emission. No Nautilus
process was launched, no catalog data was loaded, and no TEST, holdout, or future
rows were inspected.

Implementation inventory: `python/experiments/EXP-102/code/` is absent;
`python/experiments/EXP-102/analysis_code/` is absent; no EXP-102 smoke emission
exists. Existing EXP-100 processor/emission paths are reference evidence only and
are not treated as missing EXP-102 code.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Family, checkpoint, cTrader TRAIN scope, inherited AMENDMENT-2..13, 264 cells (`EXP-102:3-15`) | N/A — no EXP-102 implementation; checkpoint `design.md:143-185`, family `cf-liqswp-001.md:20-47`, universe pin `cf-liqswp-001-universe.json:2-24` | MATCHES | Current scope is the full 1D/1W catalogue, cTrader-only (`EURUSD`, `XAUUSD`, `USTEC`), INFR-021 TRAIN, with no Bybit/TEST/holdout. The prior QA 1W deviation is superseded by the current checkpoint. |
| Mechanism and derived estimand (`EXP-102:17-26`) | N/A; checkpoint `design.md:110-127`, family `cf-liqswp-001.md:109-127` | MATCHES | Prior interaction with one persistent level is the experiment-specific conditioning variable; no live prediction or cost-complete claim is introduced. |
| Object identity and non-collapsed raids (`EXP-102:28-37`) | N/A; checkpoint `design.md:129-141`, `liquidity.md:13-15,62-63` | MATCHES | Each raid remains level-linked; clustering by `level_id` is the stated uncertainty boundary. |
| Exact prior-count and outcome fields (`EXP-102:39-47`) | `python/src/xen/exp100/strategy.py:164-215`; `python/src/xen/exp100/processor.py:333-356,536-579` | DEVIATES | The frozen emission names the field `prior_raid_count`, not `previous_raid_count`; later-swing duration is `duration_ns`, not `swing_duration`. No EXP-102 mapping or derived alias is specified. |
| Retention, failure, and right-censor semantics (`EXP-102:41-47`) | Checkpoint `design.md:221-228,274-277`; `python/src/xen/exp100/processor.py:519-579,620-626` | PARTIAL | The state machine retains failures and right-censors, but EXP-102 does not define which statuses enter each outcome denominator or how null outcomes from failed/censored rows are reported. |
| Future-destroy validity (`EXP-102:49-68`) | Checkpoint `design.md:279-308`; existing generic control reader `python/experiments/EXP-100/analysis_code/scan_coverage.py:219-275` | PARTIAL | The declaration has a zero-fixed-point derangement and a non-vacuity claim. The frozen EXP-100 control is per-cell and joins on `raid_id`, but no EXP-102 analysis path says how the count-band contrast preserves exact confirmation method/reference, status, eligibility, and missingness. |
| Fixed comparator, bands, and sample-size rules (`EXP-102:70-81`) | Checkpoint `design.md:333-355`; requirements `design-requirements.md:80-128` | MATCHES | Count-zero is a direct fixed comparator, all-count rows are retained, no count gate is declared, and the channels name separate denominators. The expected-count statement remains qualitative rather than an input artifact/table. |
| EXP-102 golden trace (`EXP-102:83-90`) | Checkpoint `design.md:357-379`; existing probe `python/experiments/EXP-100/analysis_code/probe_integrity.py:262-317` | INCOMPLETE | The semantic sequence is right, but the experiment trace has no timestamps, complete input state, exact emitted field names, or hand-derived expected outputs. No EXP-102 smoke or frozen-analysis trace is available. |
| Hard/informative split (`EXP-102:92-99`) | Checkpoint `design.md:381-389`; pipeline `_pipeline-config.md:286-289,316-322` | PARTIAL | The listed hard items cover causal/fence/destroy/zero-cost concerns, but the experiment block omits explicit estimand reconciliation and no-local-accounting checks that remain binding through the checkpoint. |
| Zero-cost disclosure (`EXP-102:101-115`) | Requirements `design-requirements.md:170-188`; pipeline `_pipeline-config.md:164-195` | MATCHES | The canonical `NO_COST_CHARGED` block is present; no cost directive or cost-bearing implementation exists. |
| Amendment direction ledger (`EXP-102:7-15`) | Checkpoint `design.md:22-108`; requirements `design-requirements.md:208-220` | PARTIAL | The inherited running count `2L / 3T / 7N` matches the current checkpoint and family. The required post-final-amendment false-qualifier expectation is not recorded. |
| Frozen-analysis route (`EXP-102:5-6`) | Checkpoint `design.md:4,407-415`; family pointer `docs/experiments-docs/families/cf-liqswp-001.md:3-9,28-45` | DEVIATES | EXP-102 still declares a Nautilus `BacktestNode` vehicle, while the current state is an analysis/readiness item over the completed EXP-100 emission. No exact frozen input root, per-cell gate manifest, family estimand-gate prerequisite, or explicit no-new-run rule is in EXP-102 design. |

### Golden-trace diff

| Event | Expected from current design/checkpoint | Existing frozen-path evidence | Verdict |
|---|---|---|---|
| First raid on one high level, return recorded | First row has count 0; return does not close the raid; a 1m wick not surviving the observation OHLC is not a raid (`EXP-102:83-90`; checkpoint `design.md:360-366`) | EXP-100 processor `processor.py:256-295`; existing analysis `analysis.md:195-203` reports this A13 behavior | MATCHES for shared apparatus semantics; not an EXP-102 analysis trace |
| Second raid on the same level before opposing confirmation | Second row has count 1, shares `level_id`, and both rows remain (`EXP-102:86-90`) | Frozen schema has `prior_raid_count` (`strategy.py:167-187`); no `previous_raid_count` column or EXP-102 row-selection artifact | DEVIATES / mapping missing |
| Close-all-eligible confirmation | Latest eligible raid is primary and remains for the later swing; earlier eligible raid is `CONFIRMED_NON_PRIMARY` with its excursion retained (checkpoint `design.md:367-371`) | Processor `processor.py:432-503`; existing probe exposes raw summaries, but its level-first aggregate checks are not fully green (`analysis.md:254-263`) | PARTIAL; direct per-raid assertion is required before using this as EXP-102 evidence |
| Reference confirmation and later endpoint | Confirmation is the completed 1H reference close for the relevant stratum; later opposing reference event closes the swing (`checkpoint design.md:372-375`) | Processor `processor.py:448-503,557-579` | MATCHES in shared logic; EXP-102 does not specify how the frozen rows are filtered by confirmation method/reference |

The existing EXP-100 emission/readiness path is sufficiently specified for the
shared A13 state-machine semantics and its integrity evidence, but it is not yet
sufficiently specified as an EXP-102 frozen analysis handoff. The missing path,
field map, status denominators, and exact per-raid trace leave room for an analyst
to choose the population or columns after seeing the emission.

### Governance & boundary

- Fresh-context requirement: **PASS**. This review did not create or discuss the EXP-102 implementation; mode recorded as `subagent`.
- EXP-102 implementation: **NONE**. No code, runner, analysis code, or smoke emission exists to review; no missing code is invented here.
- Execution boundary: **PASS**. No Nautilus launch, TEST read, holdout read, future-data inspection, or re-emission was performed.
- Family registration: **PASS**. Candidate family is `REGISTERED`; HYP-002 is the registered EXP-102 question, with candidate slot 0 and 0 counted TEST reads in the current multiplicity record (`docs/signal-registry/multiplicity-registry.md:1710-1724`).
- Universe/fence: **PASS as declared**. Current checkpoint pins cTrader TRAIN (`2021-06-02T00:01:00Z` through `2023-11-22T00:00:00Z`) and manifest SHA `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` (`checkpoint design.md:145-156`); no new access was attempted.
- Holdout / TEST: **PASS as scope**. EXP-102 and the family exclude both; the requested frozen analysis must retain that boundary.
- No-local-accounting: **N/A / no EXP-102 code**. No experiment-local accounting primitive is present; the measurement emission has no trade ledger.
- Python price backtest: **PASS / not applicable**. No EXP-102 Python strategy path exists; the current review does not authorize a new price-primary run.
- Zero cost: **PASS as declared**. Canonical disclosure is present; no `COST-DIRECTIVE`, non-zero cost, or deployability/tradability claim is present in EXP-102.
- Powering strip: **PASS**. No MDE, detection floor, power curve, `UNPOWERED`, or machine value label is present; `INTEGRITY_Z` is used only for validity.
- PSR: **N/A**. No mean trade/leg-bps series or trade ledger is in this event-study scope. Any later mean trade/leg read would require same-population `psr` and `psr_n`.
- Derangement: **DECLARATION PASS; EXP-102 runtime UNVERIFIED**. The design says zero fixed points; no EXP-102 implementation exists to verify draw regeneration/rejection. Existing EXP-100 integrity evidence is not a substitute for an EXP-102 count-contrast trace.
- Amendment ledger: **REVISE**. Direction counts match; final false-qualifier expectation required by L-23 is absent. No final ledger streak of three same-direction amendments is present to flag.
- XENA, SPDR, screen conversion, and battery/eligibility rules: **N/A**. EXP-102 is not routed to those lanes and declares no seed battery, capped read, or screen-money conversion.
- Deviations: **NONE declared**. The prior 1W issue is resolved in the current checkpoint/family; no silent scope deviation was found.

Reviewed git state at `2026-08-13T18:17:52Z` (before this append; `qa-review.md` was not yet dirty):

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
 M python/experiments/EXP-103/design.md
 M python/experiments/EXP-104/design.md
 M python/experiments/INDEX.md
 M python/src/xen/exp100/config.py
 M python/src/xen/exp100/control.py
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

### Issues

1. **REVISE — frozen analysis route is not explicit.** `EXP-102/design.md:5-6` still names a Nautilus `BacktestNode` vehicle and does not pin the existing EXP-100 AMENDMENT-13 TRAIN input root, per-cell gate artifacts, family estimand-gate prerequisite, or no-new-run rule. **FAILING_ARTIFACT:** `python/experiments/EXP-102/design.md`. **REQUIRED_SKILL:** `quant-designer`. State the analysis-only handoff and exact frozen inputs.
2. **REVISE — emission field mapping is missing.** `EXP-102/design.md:41-44,77-89` names `previous_raid_count` and `swing_duration`, while the existing schema is `prior_raid_count` and `duration_ns` (`python/src/xen/exp100/strategy.py:164-215`; `processor.py:333-356,557-579`). **FAILING_ARTIFACT:** `python/experiments/EXP-102/design.md`. **REQUIRED_SKILL:** `quant-designer`. Bind every EXP-102 field to an existing frozen column or declare a deterministic derived alias and duration definition.
3. **REVISE — analysis population and missingness are under-specified.** `EXP-102/design.md:39-47,70-81` does not say how `COMPLETED`, `CONFIRMED_NON_PRIMARY`, `FAILED_BREAKOUT`, and right-censored rows enter each outcome denominator, or how null `swing_atr`/duration values are retained and reported. **FAILING_ARTIFACT:** `python/experiments/EXP-102/design.md`. **REQUIRED_SKILL:** `quant-designer`. Predeclare status, censor, null, per-cell, and per-confirmation-method handling without dropping rows.
4. **REVISE — the EXP-102 golden trace and destroy read are not reproducible from the frozen artifact.** `EXP-102/design.md:49-68,83-90` lacks exact input timestamps/states/expected columns and does not preserve confirmation method/reference in the destroy/contrast specification; the existing level-first probe caveat is recorded at `python/experiments/EXP-100/analysis.md:254-263`. **FAILING_ARTIFACT:** `python/experiments/EXP-102/design.md`. **REQUIRED_SKILL:** `quant-designer` (design) then `data-analyst` (analysis). Add a hand-derived per-raid trace and exact same-stratum derangement/read rules before interpreting count bands.
5. **REVISE — mandatory governance declarations are incomplete.** The amendment counts are present, but the final false-qualifier expectation required by `design-requirements.md:208-220` is absent; the EXP-102 control block also does not explicitly state disjointness/N/A, and its hard block omits explicit estimand-reconciliation/no-local-accounting checks. **FAILING_ARTIFACT:** `python/experiments/EXP-102/design.md`. **REQUIRED_SKILL:** `quant-designer`. Complete or explicitly inherit these clauses from the current checkpoint before readiness approval.
