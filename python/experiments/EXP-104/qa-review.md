## QA run 1 — 2026-08-11T03:52:39Z — mode: subagent — HEAD d9730b5982c8d4b4e2ed76f2f458d87e2ee70a03

Verdict: REVISE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Liquidity-level catalogue includes previous 1D/1W/4H/1H levels | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:6,56`; checkpoint `design.md:104` | DEVIATES | Checkpoint excludes 1W. |
| Sweep causal ordering and raid state | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:10-22`; checkpoint `design.md:131-153` | MATCHES | Strict excursion, inclusive return, ambiguity, ordering, and positive reversal are stated. |
| Value-gap interval and profile definition | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:43-49,67`; checkpoint `design.md:158-181` | MATCHES | Includes the strict rule `gap_span < 0.30*(VAH-VAL)`. |
| Timeframes, confirmation references, sessions, ATR, 1m input, fences and holdout | checkpoint `design.md:75-121,141-153,305-307` | MATCHES | 1H references are used for 15m/30m and 1D for 1h. |
| Controls and required emissions | checkpoint `design.md:204-253`; EXP-104 `design.md:46-55` | MATCHES | Design-only review; no implementation exists. |

### Golden-trace diff

No implementation or smoke emission exists. The design-only golden trace is consistent for the matched clauses; the 1W catalogue branch is an explicit deviation.

### Governance & boundary

- Review mode: fresh `subagent` context.
- No experiment was run and no implementation was reviewed.
- Reviewed state: 5 modified files and 11 untracked paths at the reviewer timestamp.
- Literal 100% SoT preservation is not established.

### Issues

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 2 — 2026-08-13T18:17:13Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75

Reviewed git state: `HEAD 3eb18d8683e7b5555331c88870db05d6334eea75`; dirty files were present before this append. No Nautilus process was launched; no TEST, holdout, or future rows were loaded or inspected.

Dirty files (pre-append):

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

EXP-104 implementation status: no `python/experiments/EXP-104/code/`, runner, `analysis_code/`, or `results/` exists. The only EXP-104 artifacts are `design.md` and this append-only review. The existing EXP-100 source was checked only to establish whether its frozen AMENDMENT-13 TRAIN emission can support the stated analysis; no missing EXP-104 code was invented.

Verdict: REVISE

### Design-fidelity trace

| Design clause (§ref) | Code / frozen evidence | Verdict | Notes |
|---|---|---|---|
| Family/checkpoint identity and HYP-004 question (`EXP-104/design.md:1-7`) | `cf-liqswp-001.md:1-8,109-118`; `multiplicity-registry.md:1710-1725` | MATCHES | Registered family, checkpoint, route, and HYP-004 identity agree. |
| cTrader TRAIN scope, 264-cell grid, 15m/30m→1H and 1h→1H+4H (`EXP-104/design.md:7-15,49-55`) | Checkpoint `design.md:147-177,210-228`; universe pin `cf-liqswp-001-universe.json:2-24`; family card `cf-liqswp-001.md:20-44,66-85` | MATCHES | Current working-tree checkpoint/family state includes 1W and the amended 264-cell cTrader scope; the prior QA run's 1W finding is resolved in the reviewed inputs. |
| Mechanism and object identity (`EXP-104/design.md:17-38`) | Checkpoint `design.md:110-141`; frozen EXP-100 `raids.parquet` schema and `strategy.py:175-215` | MATCHES | The stated object is the emitted level/raid/swing object, not a proxy trade. No EXP-104 implementation exists to trace beyond the frozen source. |
| Causal volatility definition (`EXP-104/design.md:40-47`) | `python/src/xen/exp100/features.py:91-174`; `python/src/xen/exp100/processor.py:102-127,256-318,321-365` | DEVIATES | The frozen source has ATR(14), a 252-value regime state, and all four regime columns, but the design does not pin whether the current completed value is included, the percentile interpolation/tie rule, or which event-time lag is authoritative. Existing bar marks use the post-update regime, while raid/excursion fields use `_last_regime` before that update. |
| Required outcome and profile reads (`EXP-104/design.md:49-55`) | Frozen `raids.parquet` schema; frozen `tpo_profiles.parquet` schema; `strategy.py:175-246` | DEVIATES | Outcome/regime fields are present, but profile/tight-gap fields are in a separate `tpo_profiles` stream keyed by `raid_id`; the design does not predeclare that join or reconcile it with checkpoint `design.md:314-328`, which says each raid record carries those fields. |
| Future-destroy control and tripwire (`EXP-104/design.md:57-79`) | `python/experiments/EXP-100/code/run_experiment.py:476-507`; `python/src/xen/exp100/control.py:100-149,172-239` | MATCHES | Existing frozen path deranges post-confirmation outcome values within asset×timeframe×configuration, checks zero fixed points, and preserves the event/regime columns. No EXP-104-specific control implementation exists. |
| Comparator, strata, and sample-size rules (`EXP-104/design.md:81-93`) | Checkpoint `design.md:333-355`; family `cf-liqswp-001.md:120-127` | MATCHES | MID is the declared within-stratum comparator, no count gate is declared, and thin rows are retained. The phrase “measured by preflight” is not sufficient for a frozen read because no preflight/source artifact is named. |
| Hard/informative split and zero-cost block (`EXP-104/design.md:104-128`) | Checkpoint `design.md:381-405`; `_pipeline-config.md:164-195`; EXP-100 run metadata `cost_model: NO_COST_CHARGED` | MATCHES | Required zero-cost content is present and no cost directive or deployability claim is present. The design does not explicitly name the existing estimand gate and no-local-accounting check as prerequisites. |
| Frozen-analysis implementation path (`EXP-104/design.md:5-6`) | `python/experiments/EXP-104/` contains no code/runner/results; existing source path is `data/nautilus_runs/EXP-100/full/` with per-cell gates under `python/experiments/EXP-100/results/execution/full/` | MISSING | The design still declares a Nautilus `BacktestNode` vehicle and does not identify the exact frozen EXP-100 input, per-cell gate, schema/hash seal, read-only analysis boundary, or “no re-emission” rule. |

### Golden-trace diff

| Design event | Expected from design | Frozen implementation evidence | Verdict |
|---|---|---|---|
| EXP-104 `GOLDEN-TRACE` (`design.md:95-102`) | A raid has a LOW label from the trailing regime; a later ATR increase may change confirmation but must not rewrite the raid label. | `processor.py:256-318` attaches raid/excursion labels before the current observation-bar ATR/regime update; `processor.py:477-478` and `567-568` attach later labels. The trace gives no timestamp, trailing values, percentile boundaries, or exact expected fields. | UNRESOLVED |
| Checkpoint T1–T3 (`checkpoint design.md:357-376`) | Observation-bar raid, same-bar return stays live, primary/non-primary settlement, and reference-close timestamp. | Existing EXP-100 golden trace and schema support those apparatus fields; they do not specify or test the EXP-104 LOW/MID/HIGH label timing. | INCOMPLETE |

No EXP-104 smoke emission exists. The single prose trace cannot be independently hand-diffed for regime provenance, and the checkpoint trace does not substitute for a regime-specific two/three-event trace.

### Governance & boundary

| Check | Evidence | Result |
|---|---|---|
| Fresh-context and record mode | This review did not contain EXP-104 implementation work; header records `mode: subagent`. | PASS |
| Registered family and read accounting | Family is `REGISTERED`; HYP-004 has candidate slot `0`; registry states TRAIN only and `0` counted TEST reads. | PASS |
| Universe/fence/holdout boundary | Current universe pin is cTrader-only with INFR-021 TRAIN bounds; review did not load TEST/holdout/future rows. | PASS |
| Frozen EXP-100 validity prerequisite | Existing 264-cell source has a family gate and per-cell gates, `raids_destroyed.parquet`, and the required regime/outcome schemas. EXP-104 design does not reference these artifacts or require the gate to pass before analysis. | REVISE |
| Mandatory declarations | Mechanism, object identity, control, tripwire, bands, sample size, golden trace, hard/informative split, and zero-cost blocks are present. | PASS with the golden-trace/path issues above |
| Amendment ledger (L-23) | Checkpoint and family carry the 2L/3T/7N directions, but no final-gate false-qualifier expectation or explicit one-directional-streak flag is declared. | REVISE |
| No research powering / machine value labels | No MDE, detection floor, power curve, `UNPOWERED`, or machine value verdict appears in EXP-104 design. | PASS |
| Derangement / one-node / local accounting | Existing destroy code enforces zero fixed points; existing runner enforces one `BacktestNode` per process; EXP-104 has no local accounting or strategy code. | PASS for the frozen source; no EXP-104 implementation to review |
| PSR | No trade/leg bps read or P&L object is declared; PSR is therefore not applicable, but the frozen-analysis design should state this explicitly. | REVISE |
| Index consistency | `python/experiments/INDEX.md:24` still says EXP-104 is amended only through 6/7/8, while current design/checkpoint/family inputs carry through AMENDMENT-13. | REVISE |

### Issues

1. **REVISE — frozen path missing.** `EXP-104/design.md:5-6` must identify the existing `data/nautilus_runs/EXP-100/full/` emission, the 264 per-cell gate files and family gate, the exact schema/config/hash seal, and a read-only analysis path; it must not imply a new `BacktestNode` run for this frozen analysis. `REQUIRED_SKILL: quant-designer`.
2. **REVISE — regime timing is not reproducible.** `EXP-104/design.md:40-47,95-102` must pin current-value inclusion, 252-window percentile/interpolation/tie rules, event-time lag, and the authoritative `regime`/`raid_regime`/`excursion_regime` fields. `REQUIRED_SKILL: quant-designer`.
3. **REVISE — golden trace is insufficient.** Add two or three timestamped regime events with exact input state, threshold values, expected labels, and persistence expectations; the checkpoint T1–T3 trace alone does not cover HYP-004. `REQUIRED_SKILL: quant-designer`.
4. **REVISE — frozen joins and integrity prerequisites are unstated.** Predeclare the `raid_id` join from `raids.parquet` to `tpo_profiles.parquet`, require the existing estimand gate and no-local-accounting check before any read, and state PSR N/A because there is no trade/leg bps series. `REQUIRED_SKILL: quant-designer`.
5. **REVISE — governance ledger/status is incomplete.** Add the final-gate false-qualifier expectation and one-directional-streak flag required by L-23; `python/experiments/INDEX.md:24` also needs a later status-only correction from 6/7/8 to 2–13 (not changed by this QA run). `REQUIRED_SKILL: quant-designer` for the ledger; index owner for the status correction.

## QA run 3 — 2026-08-14T17:09:53Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: shared fresh-context readiness review of the current full EXP-104 design against prior
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
| Read-only 264-cell AMENDMENT-14 source, gate-first, and optional profile left join (§ Frozen source/JOIN) | `design.md:12-40`; `EXP-100/results/estimand_validation.json`; `strategy.py:171-265` | MATCHES | Exact source, gates, seals, TRAIN fence, schema streams, and no-new-node boundary are pinned. |
| Causal ATR/regime mechanics and field authority (§ Mechanism) | `design.md:65-81`; `features.py:91-166`; `processor.py:285-350,470-499,587-612` | MATCHES | ATR(14), current-value inclusion, 252 window, linear 33/67 percentiles, strict ties, warmup/undefined, pre-update raid labels, and event-time fields agree. |
| Outcome/status population and binding ATR exclusion (§ Scope) | `design.md:83-105`; checkpoint `status.md:9-21`; EXP-100 report `:58-85` | MATCHES | Primary-completed population and all disclosed status/regime rows are fixed; affected excursion-derived values are excluded without repair. |
| Outcome estimators and fixed MID comparator (§ Scope/Sample size) | `design.md:100-112,166-181` | MATCHES (outcomes) | LOW-minus-MID/HIGH-minus-MID outcome contrasts have joint level-cluster mechanics, seeds, quantiles, sensitivity, empty-arm rule, and unpaired proportions. |
| Raid-frequency estimand (§ Scope/Sample size) | `design.md:96-99,176-179`; governance N4/N10 | MISSING | Count per completed observation bar is named, but the denominator population by regime, LOW/HIGH-minus-MID rate/count contrast, uncertainty estimator, zero-exposure output, and exact timestamp interval convention are not frozen. |
| Regime-label derangement (§ Control) | `design.md:119-139`; requirements §§3-4; L-28 | MATCHES for mapping | Exact strata/nullness, zero-fixed-point rejection, fixed regime labels, and unrestricted donor regime correctly destroy alignment without forced arm swaps. |
| Future-destroy hard decision and fixture (§ Tripwire) | `design.md:141-150`; governance N6b; requirements §4 | MISSING / DEVIATES | Only a synthetic +0.50 ATR fixture has a hard inequality. A surviving live regime contrast is not invalidated by an exact rule; duration/strong-move plants, SE-of-mean-destroy mechanics, and collapse fraction remain undefined. |
| Golden trace (§ Golden trace) | `design.md:186-200`; `processor.py:285-350,470-499,587-612` | PARTIAL | T1/T2 boundary and persistence logic are exact. T3 does not state the intervening 15m observations between 10:15 and the 11:00 1H event, so the asserted cached HIGH label cannot be hand-derived. |
| Amendment ledger/final null and canonical zero cost (§ Governance; § Zero cost) | `design.md:203-249,254-264`; checkpoint amendments 2-14; shared config canonical block | MATCHES | Complete 2L/3T/8N ledger, no selection machine, and verbatim canonical disclosure. |

### Golden-trace diff

| Event | Expected from design | Frozen logic | Verdict |
|---|---|---|---|
| T1 | Cached x=.80 vs .90/1.10 emits LOW before the current observation update | Raid/excursion fields read `_last_regime` before `_on_observation_bar` | MATCHES |
| T2 | Current x=1.20 is appended and the mark becomes HIGH; equal boundaries are MID | `CausalVolatilityRegime.update` and strict comparisons implement this exactly | MATCHES |
| T3 | 11:00 confirmation remains HIGH and 12:00 endpoint is MID while raid stays LOW | Event fields are not rewritten, but omitted 10:30/10:45 (and later) observation inputs determine the cached reference-event states | MISSING INPUT / PARTIAL |
| Plant/control | All authorized channels collapse and a surviving live result is invalid | Only the ATR fixture is numerically specified | MISSING |

### Governance & boundary

- Fresh-context subagent: PASS. Prior frozen path, aliases, regime mechanics, joins,
  prerequisites, PSR declaration, and ledger findings are resolved.
- Registry/fence/read accounting: PASS. HYP-004 is registered with 0 candidate slots and 0
  counted TEST reads; no TEST/holdout access occurred.
- Read-only/no implementation: PASS. EXP-100 was not run or changed; EXP-104 `analysis_code/`
  is empty and no Python backtest or local accounting path exists.
- One-node, cost, powering, PSR: PASS/N/A. No new node; frozen source and design are zero-cost;
  no live cost function, research power machinery, or trade/leg mean exists.
- Battery/null rules: PASS/N/A as declared; no selection battery, exit choice, phase-shift
  threshold, capped read, or count-based hiding.

### Issues

1. **REVISE — the hard future-destroy contract is incomplete.** `design.md:141-150` validates
   only a synthetic `swing_atr` plant. Add the same-estimator hard rule for a live observed
   regime contrast that survives destruction, exact mean-destroy SE and control/raw-fraction
   mechanics, and numeric duration/strong-move plants if those fields remain in scope.
   `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.
2. **REVISE — raid-frequency mechanics are not reproducible.** `design.md:96-99,176-179`
   must freeze the eligible observation-bar exposure denominator per regime, exact rate/count
   contrasts against MID, timestamp join interval, uncertainty, and empty/zero-exposure output.
   `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.
3. **REVISE — golden T3 omits state-changing inputs.** `design.md:195-199` must state the
   intervening observation-bar x values/boundaries through each reference event (or explicitly
   hold them fixed) so HIGH at confirmation and MID at endpoint can be derived without source
   output. `FAILING_ARTIFACT: design.md`; `REQUIRED_SKILL: quant-designer`.

## QA run 4 — 2026-08-15T00:00:00Z — mode: subagent — HEAD `12e0b63ecc1c5a16bcca220795071f5be0bf5575`

Reviewed git state: HEAD read from `.git/refs/heads/main`. `git status --short` was not executable with available read-only tools; dirty-file list is therefore not independently recorded. No analysis, execution, TEST read, holdout read, or modification was performed.

Verdict: **REVISE**

### Design-fidelity trace

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| Frozen 264-cell EXP-100 TRAIN source and gate-first boundary (§1, lines 12–44) | `python/experiments/EXP-104/results/estimand_validation.json:2-4,20-80` | MATCHES | Gate reports `blocking_pass=true`, 264 cells, pinned TRAIN fence, emission v1, and zero cost. |
| Mechanism/object identity (§2, lines 49–67) | `design.md:49-67`; `processor.py:285-315,410-435` | MATCHES | Event-study object identity and pre-update raid labels are represented. |
| ATR/regime mechanics (§2, lines 69–81) | `features.py:91-175`; `processor.py:330-350` | PARTIAL | ATR, current-value inclusion, 252-value window, linear percentiles, strict ties, and warmup/undefined states match. Same-timestamp reference-event authority does not match the golden trace; see Issue 1. |
| Population and exclusions (§3, lines 84–117) | `design.md:84-117`; frozen raid fields in `processor.py:430-437,587-612` | MATCHES | Status, primary-completed population, duration alias, and ATR-undefined exclusions are declared and emitted. |
| Frequency estimator (§3, lines 119–151) | `python/experiments/EXP-104/analysis_code/` | MISSING | The required denominator, timestamp join, block bootstrap, empty-exposure handling, and rate contrasts have no implementation. |
| Outcome estimator/report layers (§4, lines 153–190) | `python/experiments/EXP-104/analysis_code/` | MISSING | No EXP-104 analysis module or smoke output exists. |
| Future-destroy control (§5, lines 194–231) | `python/src/xen/exp100/control.py:163-258`; `EXP-100/code/run_experiment.py:476-507` | DEVIATES | Existing code is a single cyclic destroy with one seed and older grouping/columns, not the registered 2,000-draw, exact-strata EXP-104 control. |
| Tripwire (§5, lines 232–275) | `python/experiments/EXP-104/analysis_code/` | MISSING | No implementation of the fixture, outer bootstrap, same-estimator SE inequalities, or live invalidity rules. |
| Sample size, hard/informative split, PSR N/A (§6, lines 280–318) | `design.md:280-318` | MATCHES | No P&L or mean-trade/leg-bps series; PSR is correctly declared N/A. |
| Golden trace (§7, lines 322–342) | `processor.py:113-126,330-350,462-497` | DEVIATES | T1/T2 match; T3’s required pre-update confirmation state conflicts with execution order. |
| Amendment ledger and final null accounting (§8, lines 347–383) | `design.md:347-383`; registry `multiplicity-registry.md:1720-1755` | MATCHES | 2 looser / 3 tighter / 8 neutral and zero expected machine qualifiers agree. |
| Zero-cost disclosure (§9, lines 385–400) | `design.md:388-400`; validation JSON cost blocks | MATCHES | Canonical disclosure is present; validation reports `NO_COST_CHARGED` and zero cost. |

### Golden-trace diff

| Event | Expected from design | Implementation | Verdict |
|---|---|---|---|
| T1, `design.md:323-328` | Raid and excursion use cached pre-update LOW state | `_process_observation_raid_state` reads `_last_regime` before `_on_observation_bar` (`processor.py:285-315`) | MATCHES |
| T2, `design.md:329-334` | Current value is appended before ranking; strict boundary equality is MID | `CausalVolatilityRegime.update` appends before ranking and uses strict comparisons (`features.py:151-165`) | MATCHES |
| T3, `design.md:335-342` | 11:00 reference event consumes cached HIGH before the same-timestamp x=1.00 observation update | The processor completes the observation and calls `_on_observation_bar` before `_on_reference_bar` (`processor.py:113-126`). `_on_reference_bar` then records `self._last_regime` (`processor.py:462-497`). With boundaries 0.90/1.10, x=1.00 is MID, not HIGH. | **DEVIATES** |

No EXP-104 smoke emission or analysis result exists to reconcile this discrepancy.

### Governance & boundary

- **Fresh context:** PASS. This review did not contain implementation work.
- **Family/registry:** PASS. `CF-LIQSWP-001` is registered; HYP-004 has zero candidate slots and zero counted TEST reads.
- **Gate-first:** PASS from `results/estimand_validation.json` (`blocking_pass=true`, 264 cells).
- **TRAIN/holdout fence:** PASS by design and gate artifact; no TEST, holdout, or future rows were read.
- **No local accounting:** No EXP-104 code directory exists; check command was not run.
- **Python strategy backtest:** None found in EXP-104.
- **One BacktestNode:** No new node is requested; retained EXP-100 runner guards one node per process (`run_experiment.py:408-425`).
- **Derangement:** Existing EXP-100 destroy uses zero-fixed-point cyclic mappings (`control.py:100-141`), but it does not implement the EXP-104 control contract.
- **Powering/value labels:** PASS. No research MDE, detection floor, power curve, or machine value label is used.
- **PSR:** N/A; no trade, leg, or P&L estimand.
- **Amendment ledger:** PASS; no one-directional streak of three.
- **Conversion pin:** N/A; no SPDR/screen money conversion.
- **XENA:** N/A.
- **Battery/null rules:** PASS/N/A as declared; no selection battery or capped-read gate.
- **Cost model:** PASS; canonical zero-cost disclosure and gate evidence agree.
- **Source hash seal:** Note: the available gate artifact exposes per-cell config hashes but does not expose `event_log_sha256`; verify those seals from each retained run metadata before analysis.

### Issues

1. **HIGH — same-timestamp regime authority is wrong.**
   Design §2 (`design.md:69-81`) and §7 (`design.md:335-342`) require the reference event to use the immediately preceding observation state. `processor.py:113-126` updates the observation/regime before processing the reference; `processor.py:497` records the post-update regime. The golden T3 confirmation therefore becomes MID rather than the declared HIGH.
   **Required owner/change:** quant-designer and experiment-developer must resolve the contract before execution: either revise the design/golden trace to the actual post-update semantics, or implement the analysis using the explicitly required immediately preceding observation mark and add a regression fixture.

2. **HIGH — EXP-104 analysis implementation is absent.**
   Design §1 (`design.md:30-31`) requires independent analysis under `analysis_code/`; that directory is empty. Consequently frequency estimators (§3), outcome estimators (§4), reconciliation, and the registered report contract cannot be verified or executed.
   **Required owner/change:** experiment-developer must add the independent EXP-104 analysis module, deterministic smoke fixture, and emitted analysis artifacts without modifying the frozen source.

3. **HIGH — the available destroy is not the EXP-104 tripwire.**
   Design §5 (`design.md:194-275`) requires 2,000 exact-strata derangements, all outcome channels, fixture bites for ATR/duration/proportion, five-seed outer bootstraps, and `INTEGRITY_Z × bootstrap_SE` live validity checks. Existing `destroy_post_confirmation` (`python/src/xen/exp100/control.py:163-258`) performs one seed/cycle and is invoked once with older groups and only `swing_atr`, `duration_ns`, `strong_move`, and `pre_mfe_retrace` (`run_experiment.py:476-507`).
   **Required owner/change:** experiment-developer must implement the EXP-104 control in `analysis_code/`; the retained EXP-100 `raids_destroyed.parquet` must remain an apparatus receipt, not substitute evidence.

### Residual risks

- No implementation or smoke emission exists for independent verification.
- The frozen source’s same-timestamp reference semantics contradict the registered T3 trace.
- Event-log hash seals were not visible in the available gate artifact.
- Git dirty-file status was not command-verified due tooling limitations.

## QA run 5 — 2026-08-14T23:27:53Z — mode: subagent — HEAD `12e0b63ecc1c5a16bcca220795071f5be0bf5575`

Verdict: **REVISE**

Scope: single exhaustive fresh-context review of the EXP-104 analysis implementation. The
design was read before the code. Prior findings, checkpoint-019 source documents, the live
family/registry entries, the imported `xen.estimand_validation` boundary, retained EXP-100
regime mechanics, generated fixture artifact, and tests were then checked. No experiment
analysis or engine execution ran; no TEST or holdout artifact was opened.

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

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| Frozen 264-cell EXP-100 TRAIN source; gate before rows; source immutable (§1:12–32) | `analysis.py:943-1011,1085-1150` | PARTIAL | Gate, metadata, fence, event-log hash, required files, and row timestamps are checked first. The default gate is the EXP-104 copy, not the registered EXP-100 authority (`analysis.py:1181-1183`); the two files currently have identical SHA256. No source write exists. |
| Optional profile left join and complete join disclosure (§1:34–44) | `analysis.py:1061-1082,1133-1138` | DEVIATES | Keys are checked, but no left join occurs, the report is discarded, missing/extra keys are promoted to a hard failure, and undefined/profile counts are not emitted. |
| Mechanism/object identity; analysis-only event study (§2:49–69) | `analysis.py:1-7,689-750`; no order/P&L path | MATCHES | Uses retained raid/outcome rows; no Python price strategy or accounting ledger is defined. |
| Causal ATR/regime authority (§2:71–96) | `features.py:91-174`; `processor.py:95-126,285-350,462-522,540-612`; `analysis.py:1014-1058` | MATCHES | Raid uses the preceding cached mark; same-timestamp confirmation/endpoint uses the post-update mark; timestamp search is used, not bar index. |
| Complete census; completed-primary outcome population; ATR exclusion; duration alias (§3:100–124) | `analysis.py:61-69,689-697,1139-1147` | PARTIAL | Binding population, ATR exclusions for `swing_atr`/`strong_move`, and duration reconciliation exist. No implementation emits the required complete census, censor/profile reasons, duration hours, or all-regime counts. |
| Frequency exposure/rate estimator and uncertainty (§3:126–158) | `analysis.py:310-463` | PARTIAL | Preceding-mark denominator, unique IDs, MID contrasts, circular blocks, five-seed-compatible intervals, and empty exposure are implemented. No per-cell orchestration or live output calls them; the bundle combines duplicate timestamps across 264 cells (`analysis.py:1153-1164`) and cannot be passed to `_build_frequency_units` (`analysis.py:314-317`). Sensitivity lengths are not orchestrated. |
| Primary outcome contrasts, joint level-cluster bootstrap, L=5/2/10, secondary summaries (§3:118–124; §4:162–173) | `analysis.py:124-236,700-758` | DEVIATES | Mean ATR/duration and proportion contrasts exist, but only L=5 is run; `swing_price`/`swing_bps`, duration-hours, and L=2/10 outputs are absent. `analyze_regimes` also emits the unregistered MID-minus-MID arm. Bootstrap draws that omit an arm contaminate the entire interval with NaN instead of reporting finite draws/reasons. |
| Report layers, all named populations, no value labels (§4:175–196) | `analysis.py:700-750,1167-1186` | MISSING | The live command prints only a total row count. It emits no per-stratum observed/ideal handoff, no confirmation/endpoint-regime secondary strata, no evidence layers, and no registered analysis tables. |
| Exact future-destroy population and six-field outcome-block mapping (§5:201–235) | `analysis.py:239-307` | DEVIATES | Derangement and copy semantics match. Grouping adds `primary_attribution`, `profile_status`, and profile undefined reason, while the design names only status, primary-completed, and a five-bit nullness class. `_null_class` is six-bit. These changes alter donor pools, especially the retained ATR-undefined rows. |
| Singleton destroy is VOID; complete control disclosure (§5:218–235) | `analysis.py:275-307,903-932` | DEVIATES | Singleton groups are counted, but the control continues and integrity ignores the VOID count. Empirical destroyed 95% intervals are also missing. |
| Same-estimator outer-bootstrap integrity rule (§5:239–278) | `analysis.py:761-932` | PARTIAL | The two SE-family inequalities and three channels exist. Failed/partial derangements are not inputs to the hard status, and the registered production nesting is computationally infeasible at the declared defaults. |
| Pre-read planted fixture and immutable source copy (§5:270–294) | `analysis.py:466-686`; `results/fixture_integrity.json` | PARTIAL | Three planted effects, zero fixed points, source immutability, and 2,000 draws are represented. The fixture uses a separate global array remap rather than the production grouped `future_destroy`, so it cannot validate the production grouping/VOID path. |
| Sample-size context, fixed MID comparator, thin rows (§6:298–315) | `analysis.py:124-236,700-758` | PARTIAL | Counts and empty-arm reasons exist. Thin bootstrap intervals can become wholly NaN after only one empty-arm resample, and MID is incorrectly analyzed against itself. |
| Hard/informative split; no auto-value decision (§6:324–336) | `analysis.py:761-788`; repository scan | PARTIAL | No economic/value label, MDE, power floor, or count filter exists. Hard control invalidity is incomplete because failed derangements are not propagated. |
| Golden trace (§7:341–360) | retained `features.py:151-174`; `processor.py:114-126,285-350,462-522,540-612` | MATCHES | Hand trace matches the amended source semantics; see below. No analysis-specific golden regression exists. |
| Amendment ledger/final-null accounting (§8) | `design.md:363-402`; registry `multiplicity-registry.md:1720-1755` | MATCHES | 2 looser / 3 tighter / 8 neutral; no one-directional streak of three; no machine selection. |
| Canonical zero-cost disclosure (§9:404–418) | `analysis.py:643-678`; `results/fixture_integrity.json:1-10` | DEVIATES | No cost function is called, but the results artifact does not carry the required verbatim disclosure: the header, `prohibited_claims`, and `lifting` lines are absent and “document” is changed to “artifact.” |
| PSR pairing | `design.md:334-336`; code scan | N/A / MATCHES | No trade/leg mean-bps or Sharpe estimand exists. |

### Golden-trace diff

| Event | Design-derived expectation | Implementation evidence | Verdict |
|---|---|---|---|
| T1 10:00 | Raid/excursion retain cached x=0.80, LOW, before current update | `_process_observation_raid_state` captures `_atr.value` and `_last_regime` before `_on_observation_bar` (`processor.py:114-119,285-350`) | MATCHES |
| T2 10:15 | Append x=1.20 before ranking; strict 0.90/1.10 ties are MID; mark HIGH; raid stays LOW | `CausalVolatilityRegime.update` appends then applies strict comparisons (`features.py:151-174`); raid fields are not rewritten | MATCHES |
| T3 11:00–12:00 | 11:00 observation x=1.00 updates before reference, so confirmation MID; later x=1.00 updates retain MID; endpoint MID; original raid LOW | Observation processing precedes reference processing (`processor.py:114-126`); confirmation/endpoint read current `_last_regime` (`processor.py:496-497,597-598`) | MATCHES |
| Control plant | +0.50 ATR, +3.6e12 ns, +0.25 proportion all have raw bite and destroyed non-bite for every seed | Fixture artifact reports pass, but its array-only remap bypasses production group formation and singleton handling (`analysis.py:503-628`) | PARTIAL |

### Governance & boundary

- Fresh-context independence: PASS; this subagent did not implement EXP-104.
- Registry/read accounting: PASS; HYP-004 remains registered, TRAIN-only, zero counted TEST reads.
- Holdout/fence: static path PASS; no TEST/holdout file was opened. Live execution was not run.
- No local accounting: PASS — `check_no_local_accounting` returned `{'ok': True, 'banned_defs_found': []}`.
- Python price backtest / one-node rule: PASS/N/A — analysis-only; no `BacktestNode` is constructed.
- Derangement: PARTIAL — zero fixed points for mapped groups, but singleton VOID is not propagated.
- Zero cost: calculations PASS; artifact disclosure FAILS exact-text requirement.
- Neutrality/powering: PASS for value labels, MDE/power machinery, and count hiding; report completeness is MISSING.
- PSR: N/A because no trade/leg-bps or Sharpe series exists.
- XENA, conversion pin, battery selection, capped read: N/A.
- Prior QA resolution: same-timestamp semantics, frequency definition, tripwire equations, and implementation presence are resolved in design/code; the implemented live/report path and exact control remain unresolved below.

### Issues

1. **HIGH — there is no executable live analysis or registered output.**
   `analysis.py:1167-1186` gate-checks and loads raid rows, then prints only
   `{"experiment":"EXP-104","mode":"live","rows":...}`. It never calls frequency,
   outcome, sensitivity, future-destroy, census, or report-layer functions and never writes
   their results. The frequency bundle (`analysis.py:1153-1164`) is unused and combines marks
   without cell identity, which would violate the per-cell timestamp population.
   **Required change:** add bounded per-cell/per-stratum orchestration that calls every
   registered estimator/control and writes the complete neutral results artifact; preserve the
   explicit `--live` gate and frozen source.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

2. **HIGH — the production future-destroy is not computationally executable at the registered defaults.**
   For each arm/stratum, `outer_bootstrap_integrity` nests 5 seeds × 10,000 outer
   bootstraps × 2,000 destroys (`analysis.py:837-853`) — 100,000,000 full
   `future_destroy` calls, each deep-copying the population (`analysis.py:263`). The live
   control then repeats another 10,000 mappings (`analysis.py:855-860`), before multiplying
   this across hundreds of strata. There is no vectorized or mathematically equivalent
   bounded implementation, progress reporting, checkpointing, or output orchestration.
   **Required change:** implement and prove an equivalent bounded computation that preserves
   exact seed, grouping, cluster, donor, and SE semantics; add a production-scale runtime test.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

3. **HIGH — failed derangements can be reported as valid.**
   `future_destroy` leaves every n<2 group unmapped and records `VOID_NO_DERANGEMENT`
   (`analysis.py:275-307`), but both the outer bootstrap (`analysis.py:846-863`) and final
   integrity composition (`analysis.py:927-932`) discard that status. A focused synthetic
   trace produced 4 singleton groups, `mapped_rows=0`, an unchanged output, yet the hard
   decision function has no derangement-validity input and can return
   `ATTESTED_OR_NOT_APPLICABLE` (`analysis.py:761-788`). This contradicts design §5, where a
   failed derangement is invalidity.
   **Required change:** propagate per-draw/group VOID and mapping completeness into the hard
   status; never attest an affected stratum/channel when any required destroy cannot run.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

4. **HIGH — the production control population silently differs from the registered control.**
   Design §5 fixes grouping to status × primary-completed × five-bit outcome nullness after
   the exact market stratum. Code additionally groups by `primary_attribution`,
   `profile_status`, and profile undefined reason and builds a six-bit tuple
   (`analysis.py:239-273`). The source raid schema has no `profile_status`, while
   `profile_undefined_reason` splits retained ATR-undefined duration rows into different donor
   pools. This changes the null distribution and can increase singleton VOID groups.
   **Required change:** implement the exact registered keys and five-bit nullness class, or
   route a justified design amendment through `quant-designer` before changing the code.
   `FAILING_ARTIFACT: analysis_code/analysis.py` (or `design.md` if the operator changes the contract);
   `REQUIRED_SKILL: experiment-developer` (or `quant-designer`).

5. **HIGH — thin-stratum bootstrap intervals are corrupted by NaN draws.**
   `clustered_contrast_bootstrap` stores `EMPTY_ARM` resamples as NaN, then applies ordinary
   `np.quantile`/`np.std` to the full array (`analysis.py:207-234`). One empty-arm draw makes
   the entire seed interval and SE NaN. A two-cluster focused trace with one LOW and one MID
   observation reproduced `[nan, nan]` despite a finite raw contrast. Counts of invalid draws
   are not reported. The same contamination reaches outer integrity SEs
   (`analysis.py:839-863`).
   **Required change:** predeclare and implement explicit finite-draw/reason accounting that
   retains the row and counts; compute intervals only under the design-approved bootstrap
   semantics, without hiding thin strata.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`
   (and `quant-designer` only if the empty-resample rule needs design clarification).

6. **HIGH — required outcome and population layers are missing or altered.**
   `analyze_strata` runs only L=5 and only `swing_atr`, `swing_duration_ns`, and
   `strong_move` (`analysis.py:718-723`); it omits L=2/L=10 sensitivities, finite
   `swing_price`/`swing_bps` summaries, hours, complete census/exclusions, and secondary
   confirmation/endpoint-regime strata. `analyze_regimes` also emits MID-minus-MID
   (`analysis.py:753-758`), although the registered contrasts are only LOW/HIGH-minus-MID.
   Destroyed empirical 95% intervals required by §5 are absent (`analysis.py:903-926`).
   **Required change:** emit exactly every registered primary, secondary, sensitivity,
   census, and control disclosure, and remove the unregistered self-comparison.
   `FAILING_ARTIFACT: analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

7. **HIGH — source/report compliance evidence is discarded or incomplete.**
   The optional profile contract is checked as a hard exact one-to-one join but never joined
   or reported (`analysis.py:1061-1082,1133-1138`), contrary to §1's left-join and disclosure
   rule. The generated results artifact also abbreviates the mandatory zero-cost disclosure
   and omits `prohibited_claims` and `lifting` (`fixture_integrity.json:4-10`;
   writer at `analysis.py:643-652`).
   **Required change:** preserve and emit join/missing/extra/undefined evidence with the
   registered left-join semantics, and embed the canonical disclosure verbatim in every
   result document.
   `FAILING_ARTIFACT: analysis_code/analysis.py, results/fixture_integrity.json`;
   `REQUIRED_SKILL: experiment-developer`.

No Critical/REJECT-class holdout, look-ahead, local-accounting, Python-backtest, cost-charge,
or machine-value-label violation was found in the reviewed static path. The seven HIGH issues
above block approval and should be fixed together before the operator's sole execution decision.

### Focused checks run

```text
uv run pytest -q tests/test_exp10x_analysis_contract.py -k 'exp104 or fixture_contract'
  5 passed, 11 deselected
uv run ruff check experiments/EXP-104/analysis_code/analysis.py tests/test_exp10x_analysis_contract.py
  All checks passed!
python/.venv/bin/python -m py_compile python/experiments/EXP-104/analysis_code/analysis.py
PYTHONPATH=python/src python/.venv/bin/python -c '...check_no_local_accounting(...)'
  {'ok': True, 'banned_defs_found': []}
focused synthetic traces: thin two-cluster bootstrap; singleton destroy groups
SHA256 comparison: EXP-100 and EXP-104 estimand_validation.json both
  1593851873c318f3040fe1f04cedb8460dcb86470a296821548015079ffd3488
```
