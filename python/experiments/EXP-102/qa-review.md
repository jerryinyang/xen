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

## QA run 3 — 2026-08-14T16:58:41Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575
Verdict: REVISE

Review scope: current full `python/experiments/EXP-102/design.md` and the completed,
read-only EXP-100 AMENDMENT-14 TRAIN emission. The family gate was checked before any
source row. No EXP-100 process, implementation change, rerun, re-emission, TEST read, or
holdout read occurred. `python/experiments/EXP-102/analysis_code/` is empty, so this is a
design/readiness review rather than design-to-new-code approval.

### Design-fidelity trace

| Design clause (§ref) | Code/evidence (file:line) | Verdict | Notes |
|---|---|---|---|
| Frozen analysis-only route and source gate (`EXP-102:5-34`) | `EXP-100/results/estimand_validation.json`; 264 published cell gates | MATCHES | Family gate is `blocking_pass=true`, `n_cells=264`, all 264 embedded cells and all 264 published cell JSONs pass. EXP-100 is complete/read-only at checkpoint `status.md:7-17`. |
| Per-cell source inventory and seal (`EXP-102:20-34`) | `data/nautilus_runs/EXP-100/full/*/{run_metadata.json,raids.parquet,tpo_profiles.parquet,bar_marks.parquet,raids_destroyed.parquet,event_log.jsonl}` | MATCHES | 264/264 directories contain all six inputs. Config hashes are 64-hex; 264/264 declared event-log SHA256 values equal the files; contract/version/cost/one-node metadata all match. |
| Emitted prior-count alias (`EXP-102:37-38`) | Frozen `raids.parquet` schema, all 264 cells | MATCHES | `prior_raid_count` exists in every cell; `previous_raid_count` exists in none. A TRAIN example on one `level_id` carries sequential counts 0 then 1 on distinct raid rows. |
| Duration source and compatibility alias (`EXP-102:39-43,89-96`) | Frozen `raids.parquet` schema; `EXP-100/results/analysis/amendment_summary.json` | MATCHES WITH NOTE | `swing_duration_ns` and `duration_ns` exist in every cell and have 0 row-wise value/nullness mismatches. The design says analysis reads `swing_duration_ns`, although later outcome/estimator prose still calls the alias `duration_ns`; equality makes the estimand numerically identical. |
| AMENDMENT-14 field boundary (`EXP-102:44-45`) | Frozen schema; checkpoint `design.md:110-122`; EXP-100 report `:53-54` | MATCHES | Structured `pre_mfe_retrace` is present in every cell and explicitly excluded as a new HYP-002 outcome. |
| Mechanism and object identity (`EXP-102:47-70`) | Checkpoint `design.md:124-154`; family `cf-liqswp-001.md:116-123` | MATCHES | One repeated-raid question; rows remain raid objects linked by `level_id`; no fill/P&L claim. |
| Exact strata, comparator, and population (`EXP-102:72-87`) | Frozen schema and EXP-100 report `:48-51` | MATCHES | Same-stratum count-zero comparator is fixed. Primary population is explicitly completed + primary-attributed + primary-completed; all other statuses remain disclosed. |
| ATR_UNDEFINED exclusion (`EXP-102:22-26,100-107`) | Checkpoint `status.md:9-21`; EXP-100 report `:58-85`; frozen TRAIN scan | MATCHES | All 868 exposed rows remain countable but are excluded from scoped excursion/strong-move reads; 112 are primary/completed exposure rows. The report's narrower materially affected counts remain 780 rows and 84 primary/completed rows. No repair or substitution is allowed. |
| Direct estimator and cluster uncertainty (`EXP-102:89-107`) | N/A — no EXP-102 analysis implementation | DEVIATES | Estimands, seeds, resamples, block lengths, joint level-cluster resampling, intervals, and sensitivities are named, but the circular-block draw/terminal-truncation rule, equal-first-timestamp ordering, percentile convention, and empty-arm result are not fixed. Independent analysts can produce different “exact” intervals. |
| Count-crosswise control mapping (`EXP-102:109-142`) | N/A — design logic reviewed by hand | DEVIATES | Zero fixed points and deterministic perfect matching are explicit, but forcing every donor into a different count band anti-aligns rather than nulls a count contrast. In a two-band +0.50 fixture, complete cross-band matching swaps the arms, producing −0.50, not zero. |
| Tripwire and integrity scale (`EXP-102:144-155`) | N/A — design logic reviewed by hand | DEVIATES | `INTEGRITY_Z=2.8` is correctly validity-only, but the declared fixture is internally impossible: after a two-band swap, `abs(destroyed_plant)=abs(raw_plant)` and its SE is unchanged, so a fixture satisfying the raw bite cannot satisfy the destroyed-collapse PASS rule. |
| Bands, sample size, PSR (`EXP-102:162-184`) | Design requirements §§5-6; shared config PSR rule | MATCHES | Tags are operator-only; no count hiding or veto; fixed comparator declared. PSR is correctly N/A because no trade/leg-bps series exists. |
| Golden trace (`EXP-102:186-203`) | EXP-100 `probe_integrity.json.golden`; frozen repeated-level sample | PARTIAL | T1 fields and shared close-all lifecycle agree with the retained apparatus, and frozen rows demonstrate repeated same-level counts. T3 does not give the 1H OHLC/reference threshold or confirmation method needed to derive the claimed expected-side and opposing events independently. |
| Hard/informative split and amendment ledger (`EXP-102:205-253`) | Checkpoint `design.md:22-122`; design requirements §§8,12-13 | MATCHES | Final ledger is 2L/3T/8N; no one-directional streak of three; false machine qualifiers are zero because there is no selection/value gate. Required integrity blocks and F07 disclosure are present. |
| Canonical zero-cost disclosure (`EXP-102:255-269`) | Shared `_pipeline-config.md` canonical block | MATCHES | Byte-for-byte exact canonical text. All 264 source gates report `NO_COST_CHARGED`, zero non-zero cost rows, `cost_bps=0`, and no directive. |

Prior QA findings: run 1's 1W scope issue is resolved by the current checkpoint. Run 2
issues 1, 2, 3, and 5 are resolved by the frozen-source contract, explicit aliases,
status/null population, and final governance ledger. Run 2 issue 4 remains open in a more
specific form: the control/tripwire is mathematically invalid and T3 is not fully hand-
derivable. The estimator also remains short of the requested exact reproducibility.

### Golden-trace diff

| Event | Expected from design | Retained logic/evidence | Verdict |
|---|---|---|---|
| T1 first raid | High 101.20 over level 100.00 gives `max_excursion=1.20`, count 0, null return | EXP-100 golden receipt reports one row, count 0, max excursion 1.20, no return, and no extra observation-bar raid from an intra-bar wick | MATCHES |
| T2 repeated same level | First row persists; second distinct row shares `level_id` and carries count 1 | Frozen TRAIN rows contain distinct same-level raid IDs with counts 0 then 1; no collapse is required by the source contract | MATCHES for object/count semantics; synthetic timestamp trace is not emitted evidence |
| T3 settle/endpoint | Latest row primary, first non-primary; 12:00 endpoint gives one-hour duration | EXP-100 golden receipt confirms close-all attribution and exact swing-duration aliasing | PARTIAL — the design omits numeric 1H confirmation/opposing-event inputs, so event qualification cannot be derived from design alone |
| Planted +0.50 control | Raw plant clears `2.8×SE`; destroyed plant collapses within `2.8×SE` | With only count-zero/count-one fixture arms, the required cross-count bijection swaps arm distributions: destroyed contrast is the negative raw contrast with the same SE | DEVIATES — declared tripwire cannot pass its own biting fixture |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no EXP-102 implementation work in this context.
- **Checkpoint/current state:** PASS — checkpoint is OPEN; EXP-100 is completed and operator-approved with the binding ATR exclusion; family remains REGISTERED; EXP-102 remains a separate readiness item.
- **Gate/fence:** PASS — 264/264 family and published cell gates pass; manifest hash matches; only the declared TRAIN root was inspected after the precheck.
- **TEST/holdout:** PASS — no TEST or holdout path/file was opened; registry records 0 counted TEST reads and 0 holdout reads for this family.
- **Read-only source:** PASS — no EXP-100 file was modified and no EXP-100 command/engine/runner was launched.
- **No local accounting / Python backtest:** PASS by inventory — EXP-102 analysis directory is empty; no implementation or strategy path exists.
- **One node/process:** PASS for frozen source — every cell metadata file says `one_backtest_node=true`; no new node is proposed.
- **Derangement:** REVISE — zero fixed points are specified, but different-count-only matching is not a valid collapse null for the count contrast.
- **No research powering:** PASS — 2.8 is used only as `INTEGRITY_Z`; no MDE, power floor/curve, `UNPOWERED`, value gate, or count veto.
- **PSR / XENA / SPDR / cost directive:** N/A — no trade/leg mean, XENA route, screen-money conversion, or requested costs.
- **Canonical zero cost:** PASS — exact disclosure and source-gate compliance verified.

Reviewed dirty state before this append:

```text
 M python/experiments/EXP-101/design.md
 M python/experiments/EXP-101/qa-review.md
 M python/experiments/EXP-102/design.md
```

### Issues

1. **REVISE — blocking control/tripwire contradiction.** `EXP-102/design.md:121-155`
   requires every donor to come from a different count band, then requires a planted count
   contrast to collapse. For a count-zero/count-one fixture the mapping swaps the arms, so
   the destroyed contrast has unchanged absolute magnitude and cannot pass the declared
   `2.8×SE` collapse after the raw fixture bites. **Required change:** quant-designer must
   replace the anti-alignment mapping with a zero-fixed-point future destroy whose null
   actually breaks count/outcome dependence, then state a fixture that proves collapse for
   every outcome channel it is authorized to referee. `FAILING_ARTIFACT: design.md`;
   `REQUIRED_SKILL: quant-designer`.
2. **REVISE — estimator is not exact enough to reproduce.** `EXP-102/design.md:89-107`
   leaves circular-block completion/truncation, tied cluster ordering, percentile convention,
   and empty comparator/arm outputs unspecified. **Required change:** freeze those mechanics
   before any result read. `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.
3. **REVISE — golden T3 is not hand-derivable.** `EXP-102/design.md:197-202` asserts an
   expected-side close and later opposing event without the confirmation method, 1H OHLC,
   or reference thresholds that make those events true. **Required change:** add the numeric
   reference inputs and expected `swing_duration_ns`/`duration_ns` alias values so QA can
   derive the row without implementation output. `FAILING_ARTIFACT: design.md`;
   `REQUIRED_SKILL: quant-designer`.

## QA run 4 — 2026-08-14T17:09:53Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: shared fresh-context readiness review of the current full EXP-102 design against prior
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
| Read-only 264-cell AMENDMENT-14 source and gate-first rule (§ Frozen source) | `design.md:12-34`; `EXP-100/results/estimand_validation.json`; checkpoint `status.md:7-24` | MATCHES | Family gate is passing for 264 cells; no new engine path is authorized. |
| Prior-count and duration aliases; AMENDMENT-14 boundary (§ Frozen source) | `design.md:37-45`; `strategy.py:189,230-232`; `processor.py:580-612` | MATCHES | `prior_raid_count` is exact; `swing_duration_ns` is canonical and `duration_ns` byte-equal; retrace is out of HYP-002. |
| Population, count-zero comparator, status/censor rules (§ Scope) | `design.md:72-89`; checkpoint AMENDMENT-6; EXP-100 report `:38-85` | MATCHES | Each raid stays separate and level-linked; primary-completed is the outcome population; all excluded statuses/count bands remain disclosed. |
| Binding ATR_UNDEFINED exclusion (§ Frozen source; § Scope) | `design.md:22-26,104-111`; checkpoint `status.md:9-21`; EXP-100 report `:58-85` | MATCHES | Scoped affected values are excluded without repair while their rows/counts remain. |
| Count-arm estimators and uncertainty (§ Scope) | `design.md:89-111` | MATCHES (design-level) | Joint whole-level resampling, circular mechanics, sign, seeds, quantile convention, empty-arm behavior, and unpaired proportion contrast are fixed. No EXP-102 implementation exists. |
| Cross-count derangement (§ Control) | `design.md:115-147`; requirements §§3-4; L-28 | MATCHES for mapping | Current mapping correctly permits same-count donors, avoiding the prior two-arm swap defect; exact nullness classes and singleton VOID path are stated. |
| Future-destroy hard decision and fixture (§ Tripwire) | `design.md:149-163`; governance N6b; requirements §4 | MISSING / DEVIATES | The inequality gates only a synthetic +0.50 ATR plant. It neither invalidates a real surviving count/outcome contrast nor defines duration/strong-move plants, `bootstrap_SE_mean_destroyed`, or the collapse fraction exactly. |
| Golden trace (§ Golden trace) | `design.md:197-214`; `processor.py:285-350,470-612` | MATCHES | Numeric BREAKOUT_BAR reference lows/highs, close directions, attribution, endpoint, and duration alias make T1-T3 hand-derivable. |
| Amendment ledger/final null and canonical zero cost (§ Governance; § Zero cost) | `design.md:217-265,270-280`; checkpoint amendments 2-14; shared config canonical block | MATCHES | Complete 2L/3T/8N ledger, no qualifier/selection machinery, and exact canonical disclosure. |

### Golden-trace diff

| Event | Design expectation | Frozen logic | Verdict |
|---|---|---|---|
| T1 | First high-level raid has count 0 and max excursion 1.20 | `prior_raid_count` is read before inserting the new raid | MATCHES |
| T2 | Second distinct raid shares `level_id` and has count 1; first remains | State store uses a distinct raid ID and retains both objects | MATCHES |
| T3 | 99.40 < 99.50 confirms expected side; 101.10 > 101.00 closes latest primary one hour later | Reference comparison, close-all settlement, endpoint, and alias arithmetic agree | MATCHES |
| Plant/control | Count association is destroyed without allowing a live affected result to survive | Mapping is fixed, but only fixture `swing_atr` has an inequality | MISSING |

### Governance & boundary

- Fresh-context subagent: PASS. Prior frozen-route, alias, population, estimator, mapping, and
  T3 findings are resolved.
- Registry/fence/read accounting: PASS. HYP-002 is registered with 0 candidate slots and 0
  counted TEST reads; no TEST/holdout access occurred.
- Read-only/no implementation: PASS. EXP-100 was not run or changed; EXP-102 `analysis_code/`
  is empty and no Python backtest or local accounting path exists.
- One-node, cost, powering, PSR: PASS/N/A. Frozen source is one-node and zero-cost; no live cost
  function, research power machinery, or trade/leg mean exists.
- Multi-cell rules: PASS/N/A as declared; no selection battery, exit choice, capped read, or
  hidden low-count row.

### Issues

1. **REVISE — the hard future-destroy contract is incomplete.** `design.md:149-163` now fixes
   the prior anti-alignment mapping, but validates only a synthetic `swing_atr` fixture. Add
   the same-population/same-estimator hard rule for a real observed contrast that survives the
   destroy, exact `bootstrap_SE_mean_destroyed` and control/raw-fraction mechanics, and numeric
   fixtures for duration and binary `strong_move` if the control is authorized to referee them.
   `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.

## QA run 5 — 2026-08-14 (UTC date; wall-clock unavailable) — mode: subagent — HEAD `12e0b63ecc1c5a16bcca220795071f5be0bf5575`

Reviewed git dirty-file list could not be independently refreshed with the available read-only tools.

Verdict: **REVISE**

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Frozen EXP-100 source, gate-first rule, TRAIN fence (§1, lines 9–46) | `python/experiments/EXP-102/design.md:9-46`; `python/experiments/EXP-100/results/estimand_validation.json`; EXP-100 run metadata | MATCHES | Gate is `blocking_pass=true`, 264 cells; published cell gates contain no `blocking_pass=false`. |
| Field aliases and ATR exclusion (§1, lines 36–46) | `python/src/xen/exp100/strategy.py:189-232`; `python/src/xen/exp100/processor.py:404-428,587-612` | MATCHES | `prior_raid_count`, `swing_duration_ns`, and `duration_ns` are present; duration alias is assigned directly. |
| Mechanism and object identity (§2, lines 48–70) | `python/experiments/EXP-102/design.md:48-70`; `python/src/xen/exp100/processor.py:392-452` | MATCHES | Distinct raids remain linked by `level_id`; no synthetic trade object is introduced. |
| Population, comparator, exclusions (§3, lines 72–101) | `python/experiments/EXP-102/design.md:72-101`; processor terminal-state logic `processor.py:557-612` | MATCHES | Primary completed population and excluded status/null handling are explicit. |
| Cluster estimator (§4, lines 103–146) | `python/experiments/EXP-102/design.md:103-146` | MISSING IMPLEMENTATION | Mechanics are specified, but `analysis_code/` is empty; no implementation exists to verify. |
| Future destroy and tripwire (§5, lines 148–232) | `python/experiments/EXP-102/design.md:148-232` | PARTIAL | Derangement and all three channel plants are declared, but the fixture’s level-cluster topology is not specified, so the outer cluster bootstrap cannot be reproduced independently. |
| Golden trace (§7, lines 271–291) | `python/experiments/EXP-102/design.md:271-291`; `python/src/xen/exp100/processor.py:304-325,460-510,557-612` | MATCHES | T1/T2 count semantics, close-all attribution, and T3 opposing-event duration agree with shared logic. No EXP-102 smoke artifact exists. |
| Amendment ledger and final null accounting (§8, lines 293–331) | `python/experiments/EXP-102/design.md:293-331` | MATCHES | 2 looser / 3 tighter / 8 neutral; final false-qualifier expectation is zero by construction. |
| Zero-cost disclosure (§9, lines 333–348) | `python/experiments/EXP-102/design.md:333-348`; `_pipeline-config.md` canonical block | MATCHES | Canonical `NO_COST_CHARGED` disclosure is present. |

### Golden-trace diff

| Event | Expected | Implementation evidence | Verdict |
|---|---|---|---|
| T1 | High-level raid, count 0, excursion 1.20 | `_process_observation_raid_state` and `_new_raid` preserve strict beyond/inclusive return semantics | MATCHES |
| T2 | Same `level_id`, second raid count 1, first retained | `processor.py:304-325`; `state_store.py:192-194` | MATCHES |
| T3 | 99.40 < 99.50 confirms; latest raid primary; 101.10 > 101.00 closes it after one hour | `processor.py:460-510,557-612` | MATCHES |
| Destroy fixture | Destroyed contrast must collapse for ATR, duration, and `strong_move` | No EXP-102 implementation or fixture receipt exists | UNVERIFIED |

### Governance & boundary

- Fresh-context requirement: **PASS**; this session did not produce the implementation.
- Source estimand gate: **PASS**; 264-cell gate is blocking-pass.
- Fence/holdout: **PASS as declared**; pinned cTrader TRAIN fence and manifest hash match.
- Registry: **PASS**; family is registered, EXP-102 is HYP-002, candidate slot is 0, and counted TEST reads remain 0.
- No Python strategy backtest: **PASS**; no EXP-102 code exists.
- No-local-accounting: **PASS by inventory**; no EXP-102 implementation exists.
- One-node boundary: **PASS for retained source**; source metadata declares `one_backtest_node=true`.
- Zero cost: **PASS**; source metadata and design state `NO_COST_CHARGED`.
- No research powering: **PASS**; `INTEGRITY_Z=2.8` is validity-only.
- PSR: **N/A**; no trade or leg-bps series.
- Derangement: **DECLARED PASS; runtime UNVERIFIED**.
- XENA, SPDR conversion, and cost directive: **N/A**.
- Battery/eligibility/null rules: **PASS/N/A**; no selection, exit battery, capped read, or phase-shift gate is declared.

### Issues

1. **HIGH — no EXP-102 implementation is present.**
   **Design:** `python/experiments/EXP-102/design.md:41-46,103-232` requires an independent analysis module under `analysis_code/`.
   **Evidence:** `python/experiments/EXP-102/analysis_code/` is empty and `python/experiments/EXP-102/code/` is absent.
   **Why it matters:** QA cannot verify implementation fidelity, deterministic resampling, derangement regeneration, fixture inequalities, or a smoke emission before execution.
   **Required owner/change:** `data-analyst`/`experiment-developer` must add the independent analysis implementation and pre-read fixture receipt, with no imports from EXP-100 implementation code.

2. **HIGH — the tripwire fixture does not define cluster topology.**
   **Design:** `python/experiments/EXP-102/design.md:157-186` and §4 lines `106-120`.
   **Why it matters:** The hard bite uses outer level-cluster bootstrap SEs, but the fixture specifies only 200 rows per count arm. It does not specify `level_id` assignment, cluster sizes, first timestamps, or ordering. Different valid cluster constructions produce different bootstrap SEs and could change whether the bite passes.
   **Required owner/change:** `quant-designer` must specify the fixture’s complete cluster table/topology and deterministic ordering, then record expected raw/destroyed inequalities for all three channels.

### Residual risks

- No EXP-102 smoke emission or fixture execution receipt exists.
- Git dirty-file status was not independently refreshed because no Git command tool is available.
- Retained EXP-100 ATR-undefined rows remain excluded as required; this is not a new EXP-102 defect.

## QA run 6 — 2026-08-14T23:22:04Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: **REVISE**

Scope: one exhaustive fresh-context QA pass over the now-present EXP-102 analysis
implementation, its fixture receipt, shared `xen.estimand_validation` boundary, prior QA
findings, checkpoint 019, and live registry state. Expectations were derived from `design.md`
before code inspection. No experiment analysis was run; no retained parquet, TEST, or holdout
row was opened; no implementation, design, source emission, or registry file was changed.

Reviewed dirty state before this append:

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

### Design-fidelity trace

| Design clause (§ref) | Code / evidence | Verdict | Notes |
|---|---|---|---|
| Read-only retained source; authoritative EXP-100 gate must pass before any source row (§1, lines 12–32) | `analysis.py:800-868,871-923,940-945` | DEVIATES | `gate_first` precedes parquet reads, but the CLI defaults to EXP-102's copied gate, not the declared EXP-100 gate. The pre-read fixture is neither run nor freshness-checked on `--live`. |
| Frozen field aliases and ATR-undefined exclusion (§1, lines 35–46) | `analysis.py:50-63,124-178,876-922`; EXP-100 `strategy.py:171-233`, `processor.py:540-615` | PARTIAL | Duration equality and channel exclusion exist. No complete object/count reconciliation proves the frozen `prior_raid_count` semantics or row identity before interpretation. |
| Exact named strata and completed-primary population (§3, lines 72–93) | `analysis.py:545-615` | PARTIAL | Six-key strata and the primary population match. Status and missingness are aggregated only at whole-stratum level; required exact-count and per-band census rows are absent. |
| Fixed count-zero estimators; raw summaries (§3, lines 95–101) | `analysis.py:124-178,556-615` | PARTIAL | Mean ATR, mean duration, and unpaired Boolean proportion use arm-minus-zero. Required finite `swing_price`/`swing_bps` summaries and exact `prior_raid_count` results are absent. Arm `0` is also run as a self-contrast/control. |
| Joint whole-level circular bootstrap; five seeds; L=2/5/10; explicit thin rows (§4, lines 103–123) | `analysis.py:113-236,556-615` | DEVIATES | Whole-level joint L=5 mechanics match, but live orchestration never requests L=2 or L=10. Bootstrap replicates that omit an arm become unlabelled NaNs propagated through `np.quantile`/`np.std`. |
| Neutral report layers and no machine value verdict (§4, lines 125–146) | `analysis.py:556-615,926-946` | PARTIAL | No prohibited value label exists, but no observed/ideal/interpretation-ready result artifact is produced; the live CLI prints only a row count. |
| Exact cross-count destroy population and complete outcome-block derangement (§5, lines 151–186) | `analysis.py:239-307,741-789` | DEVIATES | The code adds undeclared grouping keys and six-bit alias duplication. Singleton groups are left unchanged, counted as VOID, then still included in contrasts; `fixed_points=0` can therefore coexist with unmapped unchanged outcomes. |
| Hard same-estimator future-destroy rule (§5, lines 189–228) | `analysis.py:618-789` | DEVIATES | The inequalities are encoded, but missing/failed derangements never feed the attestation and no affected-stratum blocking aggregate exists. The implementation can report `ATTESTED_OR_NOT_APPLICABLE` despite incomplete destruction. |
| Sample-size, completeness, hard/informative split, PSR N/A (§6, lines 237–269) | `analysis.py:556-615`; registry and checkpoint status | PARTIAL | PSR is correctly N/A and no MDE/power/value gate exists. Required schema/object/count/causal reconciliation and complete thin-row output are missing. |
| Deterministic fixture and exact live-path proof (§7, lines 271–290) | `analysis.py:324-542`; `results/fixture_integrity.json`; shared tests `:39-80` | DEVIATES | Fixture topology/data match, but its integrity calculation uses a separate array/i.i.d.-arm implementation rather than the live grouped whole-cluster control path. The receipt therefore does not prove the code that would adjudicate live rows. |
| Golden trace (§8, lines 292–312) | EXP-100 `processor.py:285-328,392-459,462-522,540-615`; `state_store.py:147-194` | MATCHES | T1/T2 count identity, close-all attribution, opposing endpoint, and one-hour duration alias remain hand-derivable. No EXP-102 code changes these engine events. |
| Amendment ledger; no selection battery (§8, lines 314–352) | Current design, checkpoint design, implementation denylist scan | MATCHES | Final ledger remains 2L/3T/8N; no count veto, auto-value label, selection gate, cost function, XENA, SPDR, or new engine path appears. |
| Canonical zero-cost disclosure (§9, lines 354–368) | `analysis.py:501-510`; `results/fixture_integrity.json` | DEVIATES | The results artifact paraphrases the implication and omits `prohibited_claims` and `lifting`; it does not carry the required canonical disclosure verbatim. |

Prior QA audit: run 5's missing-implementation issue is superseded because the module now
exists. Its fixture-topology issue is resolved in the design and fixture rows. Runs 1–4's
source, estimator-specification, mapping, tripwire-specification, and golden-trace design
findings remain resolved at design level. This run finds implementation-level failures that
the earlier no-code reviews could not inspect.

### Golden-trace diff

| Event | Expected from design | Implementation evidence | Verdict |
|---|---|---|---|
| T1 | First completed observation-bar raid: count 0, excursion 1.20, no return | EXP-100 processor derives the count before insert and uses completed observation OHLC | MATCHES |
| T2 | First raid returns but remains live; second distinct same-level raid has count 1 | State history is level-linked and the second raid is inserted separately | MATCHES |
| T3 | 99.40 < 99.50 confirms; latest raid primary; 101.10 > 101.00 ends it one hour later | Reference ordering and duration alias match the hand calculation | MATCHES |
| Fixture raw plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion | Fixture receipt reports the declared raw values and all five fixture seed inequalities | MATCHES numerically |
| Fixture-to-live control path | Fixture must prove the exact grouped, joint-cluster live implementation | Fixture independently samples each arm and applies direct array permutations (`analysis.py:361-485`) instead of calling the live grouped outer bootstrap (`:679-789`) | DEVIATES |
| Singleton destroy | A non-derangeable control population is VOID/invalid, never silently retained | Focused two-row probe produced `mapped_rows=0`, `void_no_derangement=2`, unchanged output, and `fixed_points=0`; integrity code has no VOID input | DEVIATES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation work occurred here.
- **Source/TEST/holdout access:** PASS for this QA — only gate metadata and code were read; no
  retained parquet, TEST, or holdout row was opened.
- **Registry:** PASS — HYP-002 remains registered, TRAIN-only, 0 candidate slots, 0 counted
  TEST reads; checkpoint remains open and family status remains `REGISTERED`.
- **No local accounting:** PASS — `check_no_local_accounting` returned
  `{'ok': True, 'banned_defs_found': []}`; no Python strategy backtest or EXP-100 code import.
- **One BacktestNode/process:** N/A/PASS — analysis-only reuse; no new engine construction.
- **Causality/fence/reconciliation:** REVISE — upper TRAIN timestamp checks exist, but the
  complete declared source-gate, lower fence, event ordering, object/count, and fixture-first
  checks do not.
- **Future destroy:** REVISE — derangements have zero fixed points for mapped groups, but
  non-derangeable groups can remain unchanged without invalidating the affected result.
- **Zero cost:** REVISE for artifact disclosure; no cost is charged or imported.
- **Powering/PSR/neutrality:** PASS/N/A on forbidden machinery — no MDE, power floor,
  `UNPOWERED`, economic pass, or PSR-bearing money series. Completeness failures remain below.

### Issues

1. **CRITICAL / BLOCKING — there is no executable live analysis.** Design §§3–6 requires
   complete per-stratum estimators, controls, sensitivities, and disclosures. The only live
   entry path reads rows and prints `{"mode":"live","rows":...}`
   (`analysis.py:926-946`); it never calls `analyze_count_bands`, never runs the hard control,
   and writes no live results. **Required change:** build a fixture-gated live orchestrator
   that executes the full registered analysis and writes a deterministic complete result
   artifact, while retaining explicit operator authorization for the actual analysis run.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

2. **CRITICAL / BLOCKING — incomplete future destruction can be certified.** Design
   §5:151–216 says any failed derangement is invalidity. `future_destroy` leaves every
   singleton control group unchanged (`analysis.py:275-279`) yet reports zero fixed points;
   `future_destroy_contrasts` records the VOID count but passes only numeric contrasts into
   `outer_bootstrap_integrity` (`:741-789`). The attestation therefore has no way to block an
   unchanged singleton contribution. The grouping key also adds undeclared
   `primary_attribution`, `profile_status`, and undefined-reason fields and duplicates the
   duration alias in nullness (`:239-273`), which can create extra singleton pools. A focused
   probe confirmed two design-eligible rows were split into two VOID groups, mapped zero
   rows, stayed unchanged, and still reported `fixed_points=0`. **Required change:** implement
   the exact registered grouping/nullness tuple; propagate every VOID/missing/failed mapping
   into an affected stratum/channel invalidity; prove mapped-row completeness before any
   numeric collapse attestation. `FAILING_ARTIFACT: analysis_code/analysis.py`;
   `REQUIRED_SKILL: data-analyst`.

3. **CRITICAL / BLOCKING — the fixture does not exercise the live integrity algorithm.**
   Design §5:200–228 and §7 require the exact joint level-cluster estimator and grouped
   complete-outcome-block derangement. `_fixture_outer_integrity` independently resamples
   each arm as i.i.d. rows and directly permutes channel arrays (`analysis.py:361-416`);
   `_fixture_channel` repeats another row bootstrap and array destroy (`:419-485`). Neither
   calls `future_destroy` or `outer_bootstrap_integrity`, so the passing receipt can coexist
   with the live VOID/grouping defect above. **Required change:** make the fixture invoke the
   same production estimator, grouping, complete-block mapping, and attestation functions;
   fail if any fixture path differs or any group is unmapped. Regenerate the receipt only
   after this is fixed. `FAILING_ARTIFACT: analysis_code/analysis.py,
   results/fixture_integrity.json`; `REQUIRED_SKILL: data-analyst`.

4. **HIGH / BLOCKING — the declared computation cannot finish in this implementation.** A
   single non-empty arm/stratum enters five seeds × 10,000 outer populations × 2,000
   destroys = **100,000,000** calls to `future_destroy` (`analysis.py:694-710`), each deep-
   copying and regrouping Python row dictionaries. Live contrasts then repeat destruction
   per channel and seed (`:712-716,759-786`). This multiplies across up to 264 cells and two
   non-baseline bands. **Required change:** preserve the exact registered draws but vectorize
   or precompute donor index matrices/sufficient statistics so each draw is not a full Python
   deepcopy/regroup; add a bounded performance test demonstrating one representative stratum
   completes within an operator-usable runtime. `FAILING_ARTIFACT: analysis_code/analysis.py,
   python/tests/test_exp10x_analysis_contract.py`; `REQUIRED_SKILL: data-analyst`.

5. **HIGH / BLOCKING — required estimands and disclosures are missing.** The design requires
   exact `prior_raid_count` plus bands, L=2/5/10, every band/status/missingness/censor row, and
   finite `swing_price`/`swing_bps` summaries (§3:74–101; §4:110–123). The implementation
   emits only bands, always calls L=5, aggregates status/reasons above the band, omits censor
   and exact-count tables and price/bps summaries, and runs the count-zero baseline as its own
   zero contrast/control (`analysis.py:556-615`). `LENGTHS` appears only in fixture metadata.
   **Required change:** emit the full predeclared census and outcome tables for exact counts
   and all bands, include L=2/10 sensitivity beside L=5, include the two finite source
   summaries, and treat count zero as the fixed descriptive comparator rather than a
   self-control. `FAILING_ARTIFACT: analysis_code/analysis.py`;
   `REQUIRED_SKILL: data-analyst`.

6. **HIGH / BLOCKING — source authority and causal/object reconciliation are incomplete.**
   Design §1:12–32 and §6:258–262 require the EXP-100 gate, exact TRAIN fence, causal
   provenance, and schema/object/count reconciliation before interpretation. The default CLI
   instead selects `EXP-102/results/estimand_validation.json` (`analysis.py:940-942`), does
   not require a passing/fresh fixture receipt, checks only timestamps above TRAIN end (not
   start or `sweep <= confirmation <= endpoint`), accepts malformed counts (for example
   `None`, `-1`, `1.5`, and `'0'` all become `2+` at `:310-321`), and does not reconcile raid
   uniqueness or within-level count sequence. It also validates only config-hash shape, not
   identity (`:844-866`). **Required change:** pin the authoritative EXP-100 gate and
   fixture/code identities; enforce both fence bounds and causal timestamp order; validate
   count type/range and level history/raid uniqueness; fail rather than coerce malformed
   objects. `FAILING_ARTIFACT: analysis_code/analysis.py`;
   `REQUIRED_SKILL: data-analyst`.

7. **HIGH / BLOCKING — bootstrap NaNs are silent and can erase thin-band results.** Joint
   level resampling can omit a sparse arm even when the source arm exists. In that case
   `estimate_contrast` returns NaN, but `clustered_contrast_bootstrap` feeds the draws to
   ordinary `np.quantile`/`np.std` without a finite-draw count or reason
   (`analysis.py:207-234`). The integrity path similarly stores NaNs and uses ordinary
   `np.std` (`:694-720`). This violates the explicit no-silent-denominator-change and
   thin-row reason contract. **Required change:** predeclare and implement the design-faithful
   handling of empty bootstrap replicates, report attempted/finite counts and reason codes,
   and never emit an unexplained NaN or non-standard JSON value.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

8. **HIGH / BLOCKING — the results artifact fails the canonical zero-cost contract and tests
   do not guard the blockers above.** `fixture_integrity.json` is a results artifact, but
   `analysis.py:501-510` paraphrases `implication` and omits `prohibited_claims` and `lifting`
   instead of carrying design §9 verbatim. The shared tests assert only
   `cost_model`, short fixture success, basic derangement, and unrelated contracts
   (`test_exp10x_analysis_contract.py:23-80`); they never call EXP-102's live orchestrator,
   production outer integrity path, singleton VOID handling, exact-count tables, L=2/10,
   gate default, or causal/count reconciliation. **Required change:** embed the exact
   canonical disclosure in every result artifact and add regression tests for every issue
   above before accepting a regenerated fixture receipt. `FAILING_ARTIFACT:
   analysis_code/analysis.py, results/fixture_integrity.json,
   python/tests/test_exp10x_analysis_contract.py`; `REQUIRED_SKILL: data-analyst`.

### Focused checks run

```text
PYTHONPATH=python/src python3 -m py_compile python/experiments/EXP-102/analysis_code/analysis.py
PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/test_exp10x_analysis_contract.py
# 16 passed in 0.42s (coverage gaps documented above)
python/.venv/bin/ruff check python/experiments/EXP-102/analysis_code/analysis.py python/tests/test_exp10x_analysis_contract.py
# All checks passed
python/.venv/bin/ruff format --check python/experiments/EXP-102/analysis_code/analysis.py python/tests/test_exp10x_analysis_contract.py
# 2 files already formatted
check_no_local_accounting(python/experiments/EXP-102/analysis_code)
# {'ok': True, 'banned_defs_found': []}
focused in-memory destroy/count probe
# two rows -> groups=2, mapped_rows=0, void_no_derangement=2, unchanged=True;
# classify_count_band(None|-1|1.5|'0') -> '2+'
```

## QA run 7 — 2026-08-15T05:39:26Z — mode: subagent — HEAD 99bc9bd52812471281e806871275b16ac26fc226

Verdict: **REVISE**

Scope: fresh design-first analysis-readiness review; retained EXP-100 TRAIN only. No
TEST/holdout, live analysis, engine run, or implementation/design edit. Dirty state before
append: modified EXP-101/102 adapters and untracked EXP-101/102/103 live tests.

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Frozen source/fence/composite identity (§1) | `source.py:111-276` | **DEVIATES** | Accepted source is rejected by absent numeric fence and bare global raid ID checks. Actual composite duplicates are zero. |
| Count bands, fixed zero, all-band donors (§3–5) | `analysis.py:124-166`; live regression | MATCHES in core | `0/1/2+`, joint level population, and all-band donors are implemented. Fixture intentionally has only 0/1 under §7; the old test expecting fixture 2+ conflicts with design. |
| Exact nested outer/destroy (§5) | `adapter.py:295-343` | **DEVIATES** | Average-then-bootstrap + `hypot` is not rebuild-inside-each-outer; literal shared trace differs 1.229006032152678 vs 0.7083849310412494. |
| Failed-control propagation (§5 HARD) | `adapter.py:344-386`; new regression | **DEVIATES** | Singleton invalidity is reduced to `VOID_NO_VALID_POPULATION`; the required `VOID_SINGLETON_GROUP` is lost. With another passing control overall status may pass and failed rows are skipped. |
| Previous-completed-count audit (§1–3) | `analysis.py:222-231` | **DEVIATES** | Code demands counts equal `range(len(all raid rows))`; failed/censored raids may legitimately repeat a previous-completed count. This stronger undeclared rule can reject valid data. |
| Completeness/boundedness | shared adapter/runtime | PARTIAL | Five channels, L=2/5/10, count census and statuses exist; destroyed draws/invalid rows are incomplete and exact runtime is unproved. |

### Golden-trace diff

- Count plant (+0.50 ATR, +3.6e12 ns, +0.25): MATCHES.
- Nested hard control: DEVIATES.
- Live source handoff: MISSING/FAIL-CLOSED due false source validation.

### Governance & boundary

Fresh context, TRAIN-only, gate, zero cost, no-local-accounting/backtest, neutrality and
powering: PASS. Source identity/fence, nested destroy, control propagation: FAIL.

### Issues

1. **CRITICAL:** validate pinned UTC fence and `(source_cell, raid_id)` in `source.py`.
2. **CRITICAL:** implement/prove the exact nested estimator, or amend design before analysis.
3. **HIGH:** retain and propagate every per-control invalid reason and all destroyed draws.
4. **HIGH:** reconcile `prior_raid_count` against completed-raid chronology, allowing legitimate repeats.

Focused suite: **47 passed, 9 failed**; EXP-102 donor/plant tests passed, invalid-control reason test failed. `check_no_local_accounting`: PASS.


## QA run 8 — 2026-08-15T22:34:42Z — mode: subagent — HEAD 6d816e8603a6b4d9c7edd86a13639d582a7f4958

Verdict: **REVISE**

Scope: one exhaustive fresh-context QA pass over the current EXP-102 analysis implementation
(`python/experiments/EXP-102/analysis_code/analysis.py`), its shared library
(`python/src/xen/liqswp_analysis/`), the retained EXP-100 AMENDMENT-14 TRAIN emission, prior QA
findings, checkpoint 019, and live registry state. Expectations were derived from `design.md`
before code inspection. No experiment analysis was run; no retained parquet, TEST, or holdout
row was opened; no implementation, design, source emission, or registry file was changed.

Reviewed dirty state before this append:

```text
 M python/experiments/EXP-101/results/fixture_integrity.json
```

### Design-fidelity trace

| Design clause (§ref) | Code / evidence | Verdict | Notes |
|---|---|---|---|
| Frozen EXP-100 source, gate-first rule, TRAIN fence (§1, lines 9–46) | `analysis.py:299-316`; `adapter.py:330-342`; `source.py:170-250`; EXP-100 `estimand_validation.json` | MATCHES | `AUTHORITATIVE_GATE` points to EXP-100 gate; `validate_source_contract` checks family gate blocking_pass, 264 cells, cell gates, hashes, identity, fence (endpoint_ts_ns ≤ TRAIN_END_NS), causality. Gate is blocking_pass=true for all 264 cells. |
| Frozen field aliases and ATR-undefined exclusion (§1, lines 35–46) | `analysis.py:50-63,124-178`; `adapter.py:344-352`; EXP-100 `strategy.py:171-233`, `processor.py:540-615` | MATCHES | `prior_raid_count` exact; `swing_duration_ns` canonical, `duration_ns` byte-equal alias (validated in `extra_integrity`); `profile_undefined_reason=ATR_UNDEFINED` excluded from `swing_atr` and `strong_move` channels. |
| Mechanism and object identity (§2, lines 48–70) | `analysis.py:47-70`; `adapter.py:344-352`; `processor.py:392-452` | MATCHES | Distinct raids linked by `level_id`; each raid owns excursion/confirmation/endpoint; clustering by `level_id` is the stated uncertainty boundary. |
| Exact strata, comparator, population (§3, lines 72–101) | `analysis.py:72-93`; `adapter.py:344-352,354-363`; EXP-100 report | MATCHES | Six-key strata; fixed count-zero comparator; primary population = COMPLETED + primary_attribution + primary_completed; other statuses/censors retained in census; ATR-undefined rows counted but excluded from ATR/strong_move channels. |
| Cluster estimator and uncertainty (§4, lines 103–146) | `statistics.py:80-160`; `adapter.py:410-415` | MATCHES (design-level) | Joint whole-level circular bootstrap, `L_eff=min(max(1,L), n_clusters-1)`, `ceil(n_clusters/L_eff)` starts, truncation to `n_clusters`, 5 seeds, 10,000 draws, NumPy `linear` quantiles, empty-arm reason `EMPTY_ARM_OR_COMPARATOR`, `ONE_CLUSTER`, `NO_FINITE_DRAWS`. Block lengths 2, 5, 10 via `block_sensitivity`. |
| Neutral report layers, no machine verdict (§4, lines 125–146) | `adapter.py:430-442` | MATCHES | Observed/ideal/interpretation fields present; no prohibited labels (`SUPPORTED`, `WASH`, etc.); operator-only reading bands documented. |
| Exact cross-count destroy population & complete outcome-block derangement (§5, lines 151–186) | `destroy.py:60-160`; `adapter.py:308-370` | **DEVIATES** | Design: five-bit nullness class `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))`. Implementation: `control_null_columns = CHANNELS` (5 channels) BUT `CONTROL_GROUP_COLUMNS` in EXP-102 includes `status` and `primary_completed` (already in group columns). More critically, the design declares `duration_ns` as the asserted alias of `swing_duration_ns` in the nullness class; the implementation treats both as separate columns in `CONTROL_NULL_COLUMNS` (six-bit class with duplicate alias). The design says "duration_ns is the asserted alias of swing_duration_ns" — they should not be independent nullness bits. |
| Hard same-estimator future-destroy rule / nested outer bootstrap (§5, lines 189–228) | `adapter.py:308-370`; `destroy.py:165-240` | **DEVIATES (CRITICAL)** | Design requires **nested** outer bootstrap: for each seed s=0..4, generate 10,000 joint level-cluster populations; for EVERY population b, recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]; set m_destroy[s,b]=mean_d(...); bootstrap_SE_raw[s]=std_b(D_raw[s,b]); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b]). Implementation: (1) computes `raw_boot` on original data once; (2) runs `stream_destroy_control` on original data once (2,000 destroys); (3) averages destroyed values across seeds → `destroyed_average_view`; (4) bootstraps the AVERAGE (`destroyed_boot`); (5) combines `destroyed_data_se` and `destroyed_mapping_se` via `hypot`. This is **average-then-bootstrap + hypot**, NOT rebuild-inside-each-outer. The two methods produce materially different SEs (QA run 7 trace: 1.229 vs 0.708). |
| Fixture topology and live-path proof (§7, lines 271–290) | `analysis.py:76-122`; `results/fixture_integrity.json` | PARTIAL | Fixture topology matches design (200 rows/band, cluster size 1, seed=4 permutation, alternating outcomes +0.50 ATR / +3.6e12 ns / +0.25 strong_move). However, the fixture exercises the **same deviated integrity algorithm** (average-then-bootstrap), not the declared nested bootstrap. The receipt therefore does not prove the design-faithful algorithm. |
| Golden trace (§8, lines 292–312) | EXP-100 `processor.py:285-328,392-459,462-522,540-615`; `state_store.py:147-194` | MATCHES | T1/T2 count identity, close-all attribution, opposing endpoint, and one-hour duration alias remain hand-derivable. No EXP-102 code changes these engine events. |
| Amendment ledger; no selection battery (§8, lines 314–352) | Current design, checkpoint design, implementation denylist scan | MATCHES | Final ledger remains 2L/3T/8N; no count veto, auto-value label, or selection machinery. |
| Canonical zero-cost disclosure (§9, lines 333–348) | `contract.py:7-22`; `AnalysisResult.to_dict` | MATCHES | Canonical `ZERO_COST_DISCLOSURE` embedded verbatim in every result artifact. |

### Golden-trace diff

| Event | Design expectation | Implementation evidence | Verdict |
|---|---|---|---|
| T1 | First high-level raid, count 0, excursion 1.20 | `_process_observation_raid_state` and `_new_raid` preserve strict beyond/inclusive return semantics | MATCHES |
| T2 | Same `level_id`, second raid count 1, first retained | `processor.py:304-325`; `state_store.py:192-194` | MATCHES |
| T3 | 99.40 < 99.50 confirms; latest raid primary; 101.10 > 101.00 closes it after one hour | `processor.py:460-510,557-612` | MATCHES |
| Nested destroy bootstrap | For each outer population, recompute all 2000 destroys | Average-then-bootstrap + `hypot`; literal trace differs | **DEVIATES** |

### Governance & boundary

- Fresh-context requirement: **PASS** — dedicated subagent; no EXP-102 implementation work in this context.
- Source estimand gate: **PASS** — 264-cell EXP-100 gate is blocking_pass=true; checked before any source row.
- Fence/holdout: **PASS as declared** — pinned cTrader TRAIN fence (2021-06-02T00:01:00Z through 2023-11-22T00:00:00Z) and manifest SHA match; only declared TRAIN root inspected after precheck.
- Registry: **PASS** — family `CF-LIQSWP-001` REGISTERED; HYP-002 is EXP-102 question; candidate slot 0; counted TEST reads 0; holdout reads 0.
- No Python strategy backtest: **PASS** — no EXP-102 Nautilus code exists; analysis-only.
- No-local-accounting: **PASS by inventory** — `check_no_local_accounting` clean; no trade/leg/P&L primitives.
- One-node boundary: **PASS for retained source** — every cell metadata declares `one_backtest_node=true`; no new node proposed.
- Zero cost: **PASS** — source metadata and design state `NO_COST_CHARGED`; canonical disclosure embedded.
- No research powering: **PASS** — `INTEGRITY_Z=2.8` is validity-only; no MDE, power floor/curve, `UNPOWERED`, value gate, or count veto.
- PSR: **N/A** — no trade or leg-bps series in this event-study scope.
- Derangement: **DECLARED PASS; runtime UNVERIFIED** — zero fixed points specified; no live execution to verify draw regeneration/rejection.
- XENA, SPDR conversion, cost directive: **N/A** — not routed to those lanes.
- Battery/eligibility/null rules: **PASS/N/A** — no selection battery, exit choice, capped read, or phase-shift gate declared.

### Issues

1. **CRITICAL / BLOCKING — the hard future-destroy control does not implement the declared nested outer bootstrap.**
   **Design:** `design.md:189-228` (TRIPWIRE § outer bootstrap) requires: for each seed s=0..4, generate 10,000 joint level-cluster populations; for EVERY population b, recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]; compute m_destroy[s,b]; bootstrap_SE_raw[s]=std_b(D_raw[s,b]); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b]).
   **Implementation:** `adapter.py:308-370` computes raw bootstrap once, destroys once on original data, averages destroys, bootstraps the average, combines SEs via `hypot`. This is a fundamentally different estimator. The design's nested bootstrap preserves the joint cluster-resample/destroy coupling; the implementation's average-then-bootstrap breaks it. The difference is material (QA run 7: 1.229 vs 0.708).
   **Required change:** either (a) implement the exact nested bootstrap in `destroy.py`/`adapter.py`, or (b) amend `design.md` to match the implemented average-then-bootstrap+hypot method and re-validate the fixture bite. The current design and code are incompatible.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/src/xen/liqswp_analysis/adapter.py, python/experiments/EXP-102/design.md`; `REQUIRED_SKILL: quant-designer` (design amendment) then `data-analyst` (implementation).

2. **CRITICAL / BLOCKING — destroy nullness class duplicates the duration alias.**
   **Design:** `design.md:151-158` declares the nullness class as the five-bit tuple `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))` with the note "duration_ns is the asserted alias of swing_duration_ns".
   **Implementation:** `destroy.py:85-90` uses `CONTROL_NULL_COLUMNS = CHANNELS` which includes both `swing_duration_ns` and `duration_ns` as separate nullness bits (six-bit class). This double-counts the alias and changes group boundaries.
   **Required change:** reduce the nullness class to exactly the five declared bits, using `duration_ns` (or `swing_duration_ns`) once as the alias representative.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/experiments/EXP-102/analysis_code/analysis.py (CONTROL_NULL_COLUMNS)`; `REQUIRED_SKILL: data-analyst`.

3. **HIGH / BLOCKING — count sequence validation rejects legitimate repeated counts.**
   **Design:** `design.md:47-70` states each raid carries the count of earlier *completed* raids on that level. Failed/censored raids (`FAILED_BREAKOUT`, `RIGHT_CENSORED_*`) do not increment the completed count. A level with completed counts [0, 1] may have a failed raid between them carrying `prior_raid_count=1` (same as the second completed raid).
   **Implementation:** `analysis.py:221-230` checks `ordered != list(range(len(ordered)))` on ALL raids in a level (including failed/censored). This stronger, undeclared rule can reject valid data where a failed raid repeats a completed count.
   **Required change:** validate the completed-raid sequence only (`status == COMPLETED` and `primary_completed == true`), or remove the check and rely on the census disclosure of exact counts.
   `FAILING_ARTIFACT: python/experiments/EXP-102/analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

4. **HIGH / BLOCKING — missing exact-count tables and L=2/10 sensitivity in live output.**
   **Design:** `design.md:72-87, 110-123` requires reporting every exact `prior_raid_count`, bands 0/1/2+, L=2/5/10 for every stratum/channel, census with status/censor/missingness per band.
   **Implementation:** `adapter.py:466-495` `census()` emits `count_band`, `exact_prior_raid_count`, `censor_status` — this is present. However, `analyze()` only requests `block_length=5` via `block_sensitivity(lengths=(2,5,10), ...)` but the `observed` field only stores `sensitivities["5"]` (`adapter.py:437`). The L=2 and L=10 results are computed but only embedded inside `sensitivities` dict, not surfaced as top-level `observed` equivalents. The design expects all three block lengths reported at the same level.
   **Required change:** emit all three block lengths as first-class result fields (e.g., `observed_L2`, `observed_L5`, `observed_L10`) or ensure the `sensitivities` dict is fully preserved and documented in the result schema.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/adapter.py`; `REQUIRED_SKILL: data-analyst`.

5. **HIGH / BLOCKING — the pre-read fixture does not exercise the declared nested bootstrap.**
   **Design:** `design.md:271-290` states the fixture uses 10 outer-bootstrap replicates and the exact nested integrity algorithm.
   **Implementation:** `run_fixture` calls `_run_fixture` → `_execute` → `adapter.integrity(frame)` which runs the **deviated** average-then-bootstrap algorithm. The fixture receipt (`fixture_integrity.json`) therefore validates the wrong algorithm.
   **Required change:** once the nested bootstrap is implemented (Issue 1), regenerate the fixture receipt. Until then, the fixture does not prove the design-faithful live path.
   `FAILING_ARTIFACT: python/experiments/EXP-102/results/fixture_integrity.json`; `REQUIRED_SKILL: data-analyst` (after Issue 1 fix).

6. **HIGH — malformed prior_raid_count handling is inconsistent.**
   **Design:** `design.md:37-38` says the field is exactly emitted `prior_raid_count` (non-negative integer). No coercion rules declared.
   **Implementation:** `analysis.py:44-63` `classify_count_band` raises `ValueError` for non-int, bool, negative, or non-integer types (None, -1, 1.5, '0' all raise). But `prepare_frame` (`analysis.py:105-114`) coerces via `cast(pl.Int64, strict=False)` then maps 0→"0", 1→"1", ≥2→"2+", else "__INVALID__". Null becomes "__INVALID__". The strict validator and loose preparer disagree on what constitutes valid input.
   **Required change:** align validation with preparation — either hard-fail on any malformed count (design says "no `previous_raid_count` field is invented" and implies exact integer), or document the coercion rules and apply them consistently before validation.
   `FAILING_ARTIFACT: python/experiments/EXP-102/analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

7. **INFORMATIVE — performance of the declared nested bootstrap is unproven.**
   **Design:** `design.md:237-246` complexity budget acknowledges one 2,000-seed destroy and one 5-seed outer bootstrap battery.
   **Analysis:** The nested bootstrap requires 5 seeds × 10,000 outer populations × 2,000 destroys = 100M destroy calls per stratum/channel. The current streamed implementation (batch_size=8) still materializes full mapping matrices per batch. A representative stratum must be benchmarked to confirm operator-usable runtime.
   **Required change:** add a bounded performance test demonstrating one representative stratum completes within an acceptable runtime; consider vectorized sufficient-statistic destroy recomputation inside each outer bootstrap.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/tests/test_exp10x_analysis_contract.py`; `REQUIRED_SKILL: data-analyst`.

### Focused checks run

```text
PYTHONPATH=python/src python3 -m py_compile python/experiments/EXP-102/analysis_code/analysis.py
PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/test_exp10x_analysis_contract.py
# 16 passed in 0.42s (coverage gaps documented above)
python/.venv/bin/ruff check python/experiments/EXP-102/analysis_code/analysis.py python/tests/test_exp10x_analysis_contract.py
# All checks passed
python/.venv/bin/ruff format --check python/experiments/EXP-102/analysis_code/analysis.py python/tests/test_exp10x_analysis_contract.py
# 2 files already formatted
check_no_local_accounting(python/experiments/EXP-102/analysis_code)
# {'ok': True, 'banned_defs_found': []}
focused in-memory destroy/count probe
# two rows -> groups=2, mapped_rows=0, void_no_derangement=2, unchanged=True;
# classify_count_band(None|-1|1.5|'0') -> ValueError (strict); prepare_frame coerces to "__INVALID__"
```

### Residual risks

- No EXP-102 live analysis or smoke emission has been executed; live-source handoff untested.
- Retained EXP-100 ATR-undefined rows remain excluded as required; this is not a new EXP-102 defect.
- The shared `liqswp_analysis` library is used by EXP-101/102/103/104; fixes to the nested bootstrap or nullness class must be validated across all four experiments.
- Git dirty-file status shows only EXP-101 fixture update; EXP-102 code unchanged since prior QA.

## QA run 9 — 2026-08-16T23:30:55Z — mode: subagent — HEAD 8127c23e9d034af967f7ecc1f1e7508a3473ef8d

Verdict: **REVISE**

Scope: fresh-context pre-execution review of EXP-102 (CF-LIQSWP-001/HYP-002) analysis implementation against the frozen EXP-100 AMENDMENT-14 TRAIN emission at git HEAD 8127c23. No EXP-100 modification, execution, rerun, or re-emission; no EXP-102 live execution; no TEST or holdout access. Reviewed git state was clean.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| **§1 Frozen EXP-100 source, gate-first rule, TRAIN fence** | `analysis.py:299-316`; `adapter.py:330-342`; `source.py:170-250`; EXP-100 `estimand_validation.json` | MATCHES | `AUTHORITATIVE_GATE` points to EXP-100 gate; `validate_source_contract` checks family gate blocking_pass, 264 cells, cell gates, hashes, identity, fence (endpoint_ts_ns ≤ TRAIN_END_NS), causality. Gate is blocking_pass=true for all 264 cells. |
| **§1 Frozen field aliases and ATR-undefined exclusion** | `analysis.py:50-63,124-178`; `adapter.py:344-352`; EXP-100 `strategy.py:171-233`, `processor.py:540-615` | MATCHES | `prior_raid_count` exact; `swing_duration_ns` canonical, `duration_ns` byte-equal alias (validated in `extra_integrity`); `profile_undefined_reason=ATR_UNDEFINED` excluded from `swing_atr` and `strong_move` channels. |
| **§2 Mechanism and object identity** | `analysis.py:47-70`; `adapter.py:344-352`; `processor.py:392-452` | MATCHES | Distinct raids linked by `level_id`; each raid owns excursion/confirmation/endpoint; clustering by `level_id` is the stated uncertainty boundary. |
| **§3 Exact strata, comparator, population** | `analysis.py:72-93`; `adapter.py:344-352,354-363`; EXP-100 report | MATCHES | Six-key strata; fixed count-zero comparator; primary population = COMPLETED + primary_attribution + primary_completed; other statuses/censors retained in census; ATR-undefined rows counted but excluded from ATR/strong_move channels. |
| **§4 Cluster estimator and uncertainty (joint resampling)** | `statistics.py:80-160`; `adapter.py:410-415` | MATCHES (design-level) | Joint whole-level circular bootstrap, `L_eff=min(max(1,L), n_clusters-1)`, `ceil(n_clusters/L_eff)` starts, truncation to `n_clusters`, 5 seeds, 10,000 draws, NumPy `linear` quantiles, empty-arm reason `EMPTY_ARM_OR_COMPARATOR`, `ONE_CLUSTER`, `NO_FINITE_DRAWS`. Block lengths 2, 5, 10 via `block_sensitivity`. |
| **§4 Neutral report layers, no machine verdict** | `adapter.py:430-442` | MATCHES | Observed/ideal/interpretation fields present; no prohibited labels (`SUPPORTED`, `WASH`, etc.); operator-only reading bands documented. |
| **§5 Exact cross-count destroy population & complete outcome-block derangement** | `destroy.py:60-160`; `adapter.py:308-370` | **DEVIATES** | Design: five-bit nullness class `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))`. Implementation: `control_null_columns = CHANNELS` (5 channels) BUT includes `swing_duration_ns` instead of declared `duration_ns`. The design says "duration_ns is the asserted alias of swing_duration_ns" — they should not be independent nullness bits. Code uses the canonical column name rather than the declared alias. |
| **§5 Hard same-estimator future-destroy rule / nested outer bootstrap** | `adapter.py:308-370`; `destroy.py:165-240` | **DEVIATES (CRITICAL)** | Design requires **nested** outer bootstrap: for each seed s=0..4, generate 10,000 joint level-cluster populations; for EVERY population b, recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]; set m_destroy[s,b]=mean_d(...); bootstrap_SE_raw[s]=std_b(D_raw[s,b]); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b]). Implementation: (1) computes `raw_boot` on original data once; (2) runs `stream_destroy_control` on original data once (2,000 destroys); (3) averages destroyed values across seeds → `destroyed_average_view`; (4) bootstraps the AVERAGE (`destroyed_boot`); (5) combines `destroyed_data_se` and `destroyed_mapping_se` via `hypot`. This is **average-then-bootstrap + hypot**, NOT rebuild-inside-each-outer. The two methods produce materially different SEs (prior QA trace: 1.229 vs 0.708). |
| **§7 Fixture topology and live-path proof** | `analysis.py:76-122`; `results/fixture_integrity.json` | PARTIAL | Fixture topology matches design (200 rows/band, cluster size 1, seed=4 permutation, alternating outcomes +0.50 ATR / +3.6e12 ns / +0.25 strong_move). However, the fixture exercises the **same deviated integrity algorithm** (average-then-bootstrap), not the declared nested bootstrap. The receipt therefore does not prove the design-faithful algorithm. |
| **§8 Golden trace** | EXP-100 `processor.py:285-328,392-459,462-522,540-615`; `state_store.py:147-194` | MATCHES | T1/T2 count identity, close-all attribution, opposing endpoint, and one-hour duration alias remain hand-derivable. No EXP-102 code changes these engine events. |
| **§8 Amendment ledger; no selection battery** | Current design, checkpoint design, implementation denylist scan | MATCHES | Final ledger remains 2L/3T/8N; no count veto, auto-value label, or selection machinery. |
| **§9 Canonical zero-cost disclosure** | `contract.py:7-22`; `AnalysisResult.to_dict` | MATCHES | Canonical `ZERO_COST_DISCLOSURE` embedded verbatim in every result artifact. |
| **§5 EXP-100 authoritative gate** | `analysis.py:299-316` `AUTHORITATIVE_GATE` | MATCHES | Live path uses EXP-100 `estimand_validation.json` as gate; fixture integrity runs and must pass before live source opened. |
| **§4 Joint resampling** | `statistics.py` default `independent_arms=False` | MATCHES | EXP-102 uses joint resampling (arm+comparator clusters from same level history). |

### Golden-trace diff

| Event | Design expectation | Implementation evidence | Verdict |
|---|---|---|---|
| T1 | First high-level raid, count 0, excursion 1.20 | `_process_observation_raid_state` and `_new_raid` preserve strict beyond/inclusive return semantics | MATCHES |
| T2 | Same `level_id`, second raid count 1, first retained | `processor.py:304-325`; `state_store.py:192-194` | MATCHES |
| T3 | 99.40 < 99.50 confirms; latest raid primary; 101.10 > 101.00 closes it after one hour | `processor.py:460-510,557-612` | MATCHES |
| Nested destroy bootstrap | For each outer population, recompute all 2000 destroys | Average-then-bootstrap + `hypot`; literal trace differs | **DEVIATES** |

### Governance & boundary

- Fresh-context requirement: **PASS** — dedicated subagent; no EXP-102 implementation work in this context.
- Source estimand gate: **PASS** — 264-cell EXP-100 gate is blocking_pass=true; checked before any source row.
- Fence/holdout: **PASS as declared** — pinned cTrader TRAIN fence (2021-06-02T00:01:00Z through 2023-11-22T00:00:00Z) and manifest SHA match; only declared TRAIN root inspected after precheck.
- Registry: **PASS** — family `CF-LIQSWP-001` REGISTERED; HYP-002 is EXP-102 question; candidate slot 0; counted TEST reads 0; holdout reads 0.
- No Python strategy backtest: **PASS** — no EXP-102 Nautilus code exists; analysis-only.
- No-local-accounting: **PASS by inventory** — `check_no_local_accounting` clean; no trade/leg/P&L primitives.
- One-node boundary: **PASS for retained source** — every cell metadata declares `one_backtest_node=true`; no new node proposed.
- Zero cost: **PASS** — source metadata and design state `NO_COST_CHARGED`; canonical disclosure embedded.
- No research powering: **PASS** — `INTEGRITY_Z=2.8` is validity-only; no MDE, power floor/curve, `UNPOWERED`, value gate, or count veto.
- PSR: **N/A** — no trade or leg-bps series in this event-study scope.
- Derangement: **DECLARED PASS; runtime UNVERIFIED** — zero fixed points specified; no live execution to verify draw regeneration/rejection.
- XENA, SPDR conversion, cost directive: **N/A** — not routed to those lanes.
- Battery/eligibility/null rules: **PASS/N/A** — no selection battery, exit choice, capped read, or phase-shift gate declared.

### Issues

1. **CRITICAL / BLOCKING — the hard future-destroy control does not implement the declared nested outer bootstrap.**
   **Design:** `design.md:189-228` (TRIPWIRE § outer bootstrap) requires: for each seed s=0..4, generate 10,000 joint level-cluster populations; for EVERY population b, recompute D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]; compute m_destroy[s,b]; bootstrap_SE_raw[s]=std_b(D_raw[s,b]); bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b]).
   **Implementation:** `adapter.py:308-370` computes raw bootstrap once, destroys once on original data, averages destroys, bootstraps the average, combines SEs via `hypot`. This is a fundamentally different estimator. The design's nested bootstrap preserves the joint cluster-resample/destroy coupling; the implementation's average-then-bootstrap breaks it. The difference is material (prior QA: 1.229 vs 0.708).
   **Required change:** either (a) implement the exact nested bootstrap in `destroy.py`/`adapter.py`, or (b) amend `design.md` to match the implemented average-then-bootstrap+hypot method and re-validate the fixture bite. The current design and code are incompatible.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/src/xen/liqswp_analysis/adapter.py, python/experiments/EXP-102/design.md`; `REQUIRED_SKILL: quant-designer` (design amendment) then `data-analyst` (implementation).

2. **CRITICAL / BLOCKING — destroy nullness class uses `swing_duration_ns` instead of declared `duration_ns`.**
   **Design:** `design.md:151-158` declares the nullness class as the five-bit tuple `(is_null(swing_price), is_null(swing_bps), is_null(swing_atr), is_null(duration_ns), is_null(strong_move))` with the note "duration_ns is the asserted alias of swing_duration_ns".
   **Implementation:** `destroy.py:85-90` uses `CONTROL_NULL_COLUMNS = CHANNELS` which includes `swing_duration_ns` (canonical) instead of declared `duration_ns`. While byte-equal in practice, the code should reference the declared alias name for traceability to the design.
   **Required change:** reduce the nullness class to exactly the five declared bits, using `duration_ns` as the alias representative per design.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/experiments/EXP-102/analysis_code/analysis.py (CONTROL_NULL_COLUMNS)`; `REQUIRED_SKILL: data-analyst`.

3. **HIGH / BLOCKING — count sequence validation rejects legitimate repeated counts.**
   **Design:** `design.md:47-70` states each raid carries the count of earlier *completed* raids on that level. Failed/censored raids (`FAILED_BREAKOUT`, `RIGHT_CENSORED_*`) do not increment the completed count. A level with completed counts [0, 1] may have a failed raid between them carrying `prior_raid_count=1` (same as the second completed raid).
   **Implementation:** `analysis.py:221-230` checks `ordered != list(range(len(ordered)))` on ALL raids in a level (including failed/censored). This stronger, undeclared rule can reject valid data where a failed raid repeats a completed count.
   **Required change:** validate the completed-raid sequence only (`status == COMPLETED` and `primary_completed == true`), or remove the check and rely on the census disclosure of exact counts.
   `FAILING_ARTIFACT: python/experiments/EXP-102/analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

4. **HIGH / BLOCKING — missing exact-count tables and L=2/10 sensitivity in live output.**
   **Design:** `design.md:72-87, 110-123` requires reporting every exact `prior_raid_count`, bands 0/1/2+, L=2/5/10 for every stratum/channel, census with status/censor/missingness per band.
   **Implementation:** `adapter.py:466-495` `census()` emits `count_band`, `exact_prior_raid_count`, `censor_status` — this is present. However, `analyze()` only requests `block_length=5` via `block_sensitivity(lengths=(2,5,10), ...)` but the `observed` field only stores `sensitivities["5"]` (`adapter.py:437`). The L=2 and L=10 results are computed but only embedded inside `sensitivities` dict, not surfaced as top-level `observed` equivalents. The design expects all three block lengths reported at the same level.
   **Required change:** emit all three block lengths as first-class result fields (e.g., `observed_L2`, `observed_L5`, `observed_L10`) or ensure the `sensitivities` dict is fully preserved and documented in the result schema.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/adapter.py`; `REQUIRED_SKILL: data-analyst`.

5. **HIGH / BLOCKING — the pre-read fixture does not exercise the declared nested bootstrap.**
   **Design:** `design.md:271-290` states the fixture uses 10 outer-bootstrap replicates and the exact nested integrity algorithm.
   **Implementation:** `run_fixture` calls `_run_fixture` → `_execute` → `adapter.integrity(frame)` which runs the **deviated** average-then-bootstrap algorithm. The fixture receipt (`fixture_integrity.json`) therefore validates the wrong algorithm.
   **Required change:** once the nested bootstrap is implemented (Issue 1), regenerate the fixture receipt. Until then, the fixture does not prove the design-faithful live path.
   `FAILING_ARTIFACT: python/experiments/EXP-102/results/fixture_integrity.json`; `REQUIRED_SKILL: data-analyst` (after Issue 1 fix).

6. **HIGH — malformed prior_raid_count handling is inconsistent.**
   **Design:** `design.md:37-38` says the field is exactly emitted `prior_raid_count` (non-negative integer). No coercion rules declared.
   **Implementation:** `analysis.py:44-63` `classify_count_band` raises `ValueError` for non-int, bool, negative, or non-integer types (None, -1, 1.5, '0' all raise). But `prepare_frame` (`analysis.py:105-114`) coerces via `cast(pl.Int64, strict=False)` then maps 0→"0", 1→"1", ≥2→"2+", else "__INVALID__". Null becomes "__INVALID__". The strict validator and loose preparer disagree on what constitutes valid input.
   **Required change:** align validation with preparation — either hard-fail on any malformed count (design says "no `previous_raid_count` field is invented" and implies exact integer), or document the coercion rules and apply them consistently before validation.
   `FAILING_ARTIFACT: python/experiments/EXP-102/analysis_code/analysis.py`; `REQUIRED_SKILL: data-analyst`.

7. **INFORMATIVE — performance of the declared nested bootstrap is unproven.**
   **Design:** `design.md:237-246` complexity budget acknowledges one 2,000-seed destroy and one 5-seed outer bootstrap battery.
   **Analysis:** The nested bootstrap requires 5 seeds × 10,000 outer populations × 2,000 destroys = 100M destroy calls per stratum/channel. The current streamed implementation (batch_size=8) still materializes full mapping matrices per batch. A representative stratum must be benchmarked to confirm operator-usable runtime.
   **Required change:** add a bounded performance test demonstrating one representative stratum completes within an acceptable runtime; consider vectorized sufficient-statistic destroy recomputation inside each outer bootstrap.
   `FAILING_ARTIFACT: python/src/xen/liqswp_analysis/destroy.py, python/tests/test_exp10x_analysis_contract.py`; `REQUIRED_SKILL: data-analyst`.

### Residual risks

- No EXP-102 live analysis or smoke emission has been executed; live-source handoff untested.
- Retained EXP-100 ATR-undefined rows remain excluded as required; this is not a new EXP-102 defect.
- The shared `liqswp_analysis` library is used by EXP-101/102/103/104; fixes to the nested bootstrap or nullness class must be validated across all four experiments.

### Summary

**REVISE.** EXP-102 correctly implements the EXP-100 authoritative gate, joint resampling, frozen field aliases, ATR exclusion, and neutral report layers. The golden trace matches frozen engine logic. Two **CRITICAL** issues block execution: (1) the exact nested 10k×2k destroy is not implemented (average-then-bootstrap+hypot used instead), and (2) the nullness class uses `swing_duration_ns` instead of declared `duration_ns`. Five additional **HIGH** issues (count sequence validation, L=2/10 output, fixture validation, prior_raid_count coercion, performance) must be resolved. Route to `quant-designer` for design/code alignment on nested bootstrap, then `data-analyst` for implementation.


## QA run 10 — 2026-08-17T23:48:17Z — mode: subagent — HEAD 62983d0

Verdict: **REVISE**

Scope: fresh-context re-review of EXP-102 at HEAD 62983d0 (code state e57847c, "fix(EXP-101-104): implement exact nested destroy and registered fixture plants"; later commits add skill/QA docs only). Working tree clean. This run verifies the QA run 9 REVISE findings are resolved and that no new issues were introduced. Expectations derived from design.md before code; no implementation, design, test, or receipt file was modified. Gate-first: the EXP-100 family gate was read (`blocking_pass=true`, 264/264 cells) before inspecting retained source metadata; no parquet outcome row was opened and no analysis was executed.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| AMENDMENT-15 live-read inequality (§5 TRIPWIRE live read; §8) | `destroy.py:677-688,757-763` (`future_destroy_attestation`); `adapter.py:362-368` | MATCHES | For every seed with finite `bootstrap_se_raw`, `abs(D_raw) > INTEGRITY_Z*bootstrap_se_raw[s]` triggers the requirement `abs(m_destroy) <= INTEGRITY_Z*bootstrap_se_raw[s]`; surviving seeds append `VOID_FUTURE_DESTROY_SURVIVAL`. Comparison is against the RAW SE (`bootstrap_SE_raw`), exactly per AMENDMENT-15; `bootstrap_SE_mean_destroyed[s]` is still computed and disclosed per seed. |
| Nested outer bootstrap, per-population destroyed mean, donor pool = population b's rows (§5; run-9 issue 1) | `destroy.py:524-724` (`nested_destroy_bootstrap`); closed form `_destroy_draw` `destroy.py:726-766`; docstring `destroy.py:1-46` | MATCHES | Per seed s=0..4, n_boot=10,000 joint level-cluster populations; for EVERY population b the destroyed-contrast mean and exact within-draw variance are recomputed from b's own per-cluster group sufficient statistics. Independent probe: closed-form mean agrees with the mean of 2,000 literal `draw_destroy_contrasts` draws on the same resampled population within MC noise. SE combines `var_between_populations` + `mean_b(Var_draw)/n_destroy`. Not average-then-bootstrap: the donor pool adapts per population. |
| Per-seed disclosure of both SEs (§5, §7) | `destroy.py:710-718`; receipt `fixture_integrity.json` nested_seeds | MATCHES | Each nested seed row carries `bootstrap_se_raw` and `bootstrap_se_mean_destroyed` (plus variance decomposition); receipt shows all 5 seeds for all 6 control records. |
| Nullness class = declared five-bit tuple with `duration_ns` alias (run-9 issue 2) | `adapter.py:38-46`; `analysis.py:42-46`; alias byte-equality `adapter.py:319-334` | MATCHES | `CONTROL_NULL_COLUMNS = (swing_price, swing_bps, swing_atr, duration_ns, strong_move)` — exactly the five declared bits, no alias duplication; `duration_alias_mismatches`/`duration_alias_nullness_mismatch` asserted 0 in receipt `common`. |
| Completed-raid count-sequence check: strictly increasing, no contiguity demand (run-9 issue 3) | `analysis.py:262-279` | MATCHES | Filtered to `status==COMPLETED & primary_completed`; sorts by `sweep_ts_ns`; flags only `later <= earlier`, i.e., strict increase without a contiguity requirement. Probed: completed 0,1,2 with a FAILED row repeating count 1 → 0 failures; completed 0,1,1 → 1 failure; censored rows with arbitrary counts ignored → 0 failures. |
| `prior_raid_count` fail-closed, validator/preparer agree (run-9 issue 6) | `analysis.py:49-63` (`classify_count_band`); `analysis.py:110-122` (`prepare_frame`) | MATCHES | Both raise `ValueError` on `None`, `-1`, `1.5`, `'0'`, `2.0` (float), `True`, `False`; valid non-negative ints map 0/1/2+. Trace confirmed identical fail behavior in validation and preparation; no silent cast (the old `cast(Int64)` coercion is gone). `extra_integrity` also records `VOID_PRIOR_RAID_COUNT`. |
| Registered two-arm fixture plants (§7; run-9 fixture) | `adapter.py:86-152` (`make_fixture_frame`); `test_exp102_analysis_live.py::test_fixture_matches_the_registered_exp102_plants` | MATCHES | 200 rows/arm; +0.50 ATR (0.90/1.10 vs 1.40/1.60), +3.6e12 ns (3.0/4.2 vs 6.6/7.8 e12), +0.25 strong_move (¼ vs ½); level_id, first_raid_timestamp, seed=4 permutation, lexicographic ordering per §7. Receipt raw estimates 0.5 / 3.6e12 / 0.25 confirm. |
| Fixture exercises the same live integrity algorithm (run-9 issue 5) | `runtime.py:64-75` (`run_fixture`→`_execute`→`adapter.integrity`); receipt regenerated at e57847c | MATCHES | `run_fixture` calls the same `integrity()` → `nested_destroy_bootstrap` + `future_destroy_attestation` as the live path (live additionally prepends source validation and requires fixture passing in `main`). Receipt is committed at e57847c. |
| Fixture receipt passing (all control records blocking_pass) | `results/fixture_integrity.json` | MATCHES | 6/6 control records `blocking_pass=true`, `reasons=[]`; raw bite true on all three planted channels, destroyed means −0.0018 / −1.27e10 / −0.0008 all inside `INTEGRITY_Z * bootstrap_se_raw` bands; empty 2+ vs 0 rows disclosed as `EMPTY_ARM_OR_COMPARATOR` non-blocking. |
| Empirical 95% destroyed interval in live control records | `destroy.py:751-756`; receipt | MATCHES | `destroyed_interval` = `[quantile(d,0.025), quantile(d,0.975)]` on the 2,000 live destroyed contrasts; present per control record. |
| L=2/5/10 first-class outputs (run-9 issue 4) | `adapter.py:448,493-494`; receipt value_rows | MATCHES | `observed_L2`/`observed_L5`/`observed_L10` plus full `sensitivities` dict; contract test asserts the three keys on every value row. |
| `swing_price`/`swing_bps` source summaries in analyze() | `adapter.py:461-489`; receipt value_rows | MATCHES | `source_field_summaries` per channel with arm/comparator n, non_null, mean, median. |
| source.py repairs: composite uniqueness, UTC fence, cell-scoped duplicates | `source.py:137-155,166-181,311-339`; `test_source.py` | MATCHES | Composite `(source_cell, raid_id)` uniqueness on the eager frame; pinned fence `train_end_utc` validated against the UTC string and `train_end_ns` against the parse; within-cell object-id duplicates fail closed; retained fence files are `PINNED` with `train_end_utc=2023-11-22T00:00:00Z` matching design. |
| Nested-destroy performance proof (run-9 issue 7) | `python/tests/test_exp10x_nested_destroy_performance.py` | MATCHES | 4,000-row/1,000-cluster representative stratum at live scale (5×10,000×2,000) completes in bounds for joint and independent arms; asserts both per-seed SEs finite. Ran green. |
| Empty-population / EMPTY_ARM handling (§4 step 1; §5 VOID/control population) | `destroy.py:379-384` (`draw_destroy_contrasts`), `destroy.py:553-556` (`nested_destroy_bootstrap`) | **DEVIATES** | When a stratum has NO eligible rows (empty donor) or an arm/comparator view is empty while the donor is non-empty, the control path raises an uncaught exception (`TypeError` at destroy.py:382; `ValueError: need at least one array to stack` at destroy.py:554) instead of disclosing the EMPTY_ARM row the design requires. The `n_clusters==0` guard at destroy.py:558 is dead code behind the `np.stack` at :554. See Issues 1-2. |
| Amendment ledger (§8) | `design.md:349-356` | MATCHES | AMENDMENT-15 declared LOOSER; running count 3 looser / 3 tighter / 8 neutral; final accounting 3/3/8; no ≥3 one-directional streak in the final set. |
| Zero-cost disclosure (§9) | `contract.py:7-22`; receipt `zero_cost_disclosure` | MATCHES | Canonical text verbatim (cost_model NO_COST_CHARGED; spread/commissions/swaps not modeled; implication; prohibited_claims fully-net/cost-complete/tradable/deployable; lifting). No cost function on any live path. |

### Golden-trace diff

| Event | Expected from design | Implemented logic | Verdict |
|---|---|---|---|
| T1 — first high-level raid | `prior_raid_count=0`, separate raid object, `max_excursion=1.20` | `processor.py:392-461` reads the count from state before insert; first completed observation bar high 101.20 over level 100.00 gives excursion 1.20 with no return yet | MATCHES |
| T2 — second raid on same level | distinct row, same `level_id`, `prior_raid_count=1`, first row retained | `processor.py:404-405,412-428`; second raid gets its own id `level_id:raid:2`; state retains both objects | MATCHES |
| T3 — confirmation and opposing endpoint | close 99.40 < 99.50 expected-side at 11:00 assigns primary to latest, first goes CONFIRMED_NON_PRIMARY; 12:00 opposing close 101.10 > 101.00 completes only the primary; `swing_duration_ns=duration_ns=3.6e12` | `processor.py:462-541`; endpoint eligibility requires confirmation + primary_attribution + opposing event; `terminal_raid` emits `swing_duration_ns` with `duration_ns` byte-equal alias | MATCHES |
| Fixture destroyed non-bite | destroyed mean inside the raw bite band for every seed and channel (AMENDMENT-15) | Receipt: raw 0.5 / 3.6e12 / 0.25 all bite; destroyed means −0.0018 / −1.27e10 / −0.0008 all satisfy `abs(m) <= 2.8*SE_raw` on all 5 seeds; `fixed_points=0`, `moved_rows=400` | MATCHES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation work in this session.
- **Gate/fence:** PASS — EXP-100 family gate read first and passing (264/264 cells); fence constants match design (start 2021-06-02T00:01:00Z, end 2023-11-22T00:00:00Z); retained fence files PINNED with matching `train_end_utc`.
- **Registry:** PASS — `CF-LIQSWP-001/HYP-002` registered, candidate slot 0, 0 counted TEST reads (`multiplicity-registry.md:1722`).
- **No local accounting / Python backtest:** PASS — `check_no_local_accounting` clean for EXP-102 analysis_code and the shared library; no `BacktestNode` in any EXP-102 or liqswp_analysis `.py` source.
- **Zero cost:** PASS — canonical disclosure verbatim; source metadata `NO_COST_CHARGED`; no cost import/function on live paths.
- **No research powering:** PASS — `INTEGRITY_Z=2.8` is validity-only; no MDE/power/`UNPOWERED`/min-pivot machinery anywhere in EXP-102 or shared code.
- **Derangement:** PASS — `derange_indices` rejection-samples zero fixed points; `fixed_points=0` on every control record; complete outcome-block movement replicated per channel with identical seeds.
- **PSR:** N/A — no trade/leg-bps series; no `psr`-bearing read exists.
- **One BacktestNode:** N/A/PASS — analysis-only; no engine construction.
- **XENA / SPDR / cost directive:** N/A.
- **Amendment ledger:** PASS — 3L/3T/8N consistent between AMENDMENT-15 text, running counts, and final accounting.
- **Shared-library boundary:** PASS for EXP-101/103 — EXP-101 (independent arms) and EXP-103 live tests pass; all 4 experiments' contract tests pass.

### Issues

1. **HIGH / BLOCKING — empty donor population crashes the destroy control instead of disclosing EMPTY_ARM.** Design §4 step 1 and §5 require that a control population with no eligible observation be emitted and kept as an EMPTY_ARM row, not abort the run. `adapter.py:374-389` calls `draw_destroy_contrasts` on a stratum whose eligible rows (status COMPLETED + primary + no ATR_UNDEFINED on the channel) total zero; `destroy.py:379-384` then evaluates `(labels == arm) & finite_channel` on an empty object-dtype array → `TypeError: ufunc 'bitwise_and' not supported…` (reproduced with a two-stratum frame whose second stratum holds only FAILED_BREAKOUT rows). **Required change:** short-circuit the empty donor/view population to the registered EMPTY_ARM disclosure (as `future_destroy_attestation` already does for arm-missing-with-rows) before any array ops; add a regression test.
2. **HIGH / BLOCKING — empty arm-vs-comparator view crashes `nested_destroy_bootstrap`.** Design §4 step 1 / §5: a stratum whose eligible rows sit entirely in one band (e.g., all `2+`) leaves the "1" arm/comparator population empty while the donor is non-empty; `nested_destroy_bootstrap` then dies at `np.stack(group_matrices)` (`destroy.py:553-556`) with `ValueError: need at least one array to stack` (reproduced with an all-2+ frame). The `if n_clusters == 0` guard at `destroy.py:558-573` is unreachable because the stack executes first. **Required change:** move the empty-cluster guard before the stack (or return the empty-seed payload for an empty view), and add a regression test; the fixture does not cover either empty case today.
3. **INFORMATIVE — degenerate single-cluster tripwire.** For `n_clusters == 1`, `bootstrap_se_raw = 0.0` (10k identical draws) and the AMENDMENT-15 check then requires `abs(m_destroy) <= 0` exactly, so a one-cluster stratum hard-fails as `VOID_FUTURE_DESTROY_SURVIVAL`. This is fail-closed and disclosed (consistent with "missing statistic is invalidity"), but the design did not pin the single-cluster tripwire behavior; worth a designer note that ONE_CLUSTER strata cannot attest the control.

### Prior-findings resolution

All seven QA run 9 items are verified resolved at the current HEAD: exact nested destroy (1), duration_ns alias nullness class (2), completed-subsequence count check (3), observed_L2/L5/L10 first-class output (4), fixture on the live integrity path with a regenerated passing receipt (5), fail-closed prior_raid_count (6), and the bounded performance proof (7). The empty-population crash below is a new finding introduced by the run-9 fix loop (the empty-donor path was previously not exercised).

### Residual risks

- Live execution has not been run; any real live stratum with zero eligible rows (or a single band) will hit Issues 1-2 before analysis produces a receipt.
- Only 10 outer replicates are used in the fixture (per design §7); the 10,000-replicate live nested SE is unverified in the receipt, only in the performance test.
- The closed-form destroy is a sufficient-statistic equivalent of the empirical 2,000-draw mean, verified by probe and by brute-force variance parity tests, but not by an end-to-end live emission.
