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

## QA run 6 — 2026-08-15T05:39:26Z — mode: subagent — HEAD 99bc9bd52812471281e806871275b16ac26fc226

Verdict: **REVISE**

Scope: fresh design-first analysis-readiness review; retained EXP-100 TRAIN only. No
TEST/holdout, live analysis, engine run, or implementation/design edit. Dirty state before
append: modified EXP-101/102 adapters and untracked EXP-101/102/103 live tests.

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Frozen source/gate/composite identity (§1) | `source.py:111-276`; `analysis.py:419-426` | **DEVIATES** | Default uses EXP-104 copied gate, not EXP-100 authority. Shared validation falsely rejects pinned UTC fence and globally repeated cell-local raid IDs; composite audit is clean. |
| Causal preceding-mark regime (§2–3) | `analysis.py:194-341` | MATCHES in core | Source-cell/timestamp join, preceding mark, and mismatch checks are causal. |
| Frequency one-day blocks (§3) | `analysis.py:301-324` | **DEVIATES** | Design requires base 96/48/24 for 15m/30m/1h plus half/double. Code uses 2/5/10 for every timeframe, filters warmup/undefined exposure before census, and incompletely emits empty regimes. |
| All-regime destroy donors (§5) | shared `_population_view` | **DEVIATES** | LOW-vs-MID excludes HIGH and HIGH-vs-MID excludes LOW; design pools all regime labels. |
| Exact nested 10,000×2,000 (§5) | `adapter.py:295-343` | **DEVIATES** | Average-then-bootstrap is numerically non-equivalent to rebuild-inside-outer (shared literal 1.229006032152678 vs 0.7083849310412494). |
| Per-control propagation/disclosure (§5 HARD) | `adapter.py:270-386` | **DEVIATES** | Failed controls can be hidden by passing companions; invalid rows are skipped; alias nullness mismatch and all destroyed draws are absent. |
| Secondary outcomes / boundedness (§3–6) | `analysis.py:373-395`; shared adapter | PARTIAL | Primary outcomes/censuses exist; confirmation/endpoint outcome strata are census-only. Exact production runtime unproved. |

### Golden-trace diff

- T1–T3 causal regimes: MATCHES retained engine semantics.
- Frequency uncertainty: DEVIATES (wrong block scale).
- Outcome destroy: DEVIATES (wrong donor pool and nested SE).
- Live source: MISSING/FAIL-CLOSED.

### Governance & boundary

Fresh context, TRAIN-only, passing gate, zero cost, causal join, no-local-accounting/backtest,
neutrality/powering/PSR N/A: PASS. Source, frequency, donor/nested control, completeness: FAIL.

### Issues

1. **CRITICAL:** fix UTC fence/composite identity and default to EXP-100 gate.
2. **CRITICAL:** pool LOW/MID/HIGH and implement/prove exact nested integrity semantics.
3. **HIGH:** use 96/48/24 one-day blocks plus half/double; retain warmup/undefined/empty exposure rows.
4. **HIGH:** propagate all failed controls, preserve invalid rows/reasons, emit all draws, and add declared confirmation/endpoint outcome strata.

Focused suite: **47 passed, 9 failed** (shared hard-control/source failures apply). Composite duplicates=0. `check_no_local_accounting`: PASS.

## QA run 7 — 2026-08-16T23:30:55Z — mode: subagent — HEAD 8127c23e9d034af967f7ecc1f1e7508a3473ef8d

Verdict: **REVISE**

Scope: fresh-context pre-execution review of EXP-104 (CF-LIQSWP-001/HYP-004) analysis implementation against the frozen EXP-100 AMENDMENT-14 TRAIN emission at git HEAD 8127c23. No EXP-100 modification, execution, rerun, or re-emission; no EXP-104 live execution; no TEST or holdout access. Reviewed git state was clean.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| **§1 Frozen source authority & gate-first** | `source.py:155-348` `validate_source_contract` | MATCHES | Family gate checked before any source rows; 264 cells verified; config_hash, event_log_sha256, NO_COST_CHARGED, one_backtest_node, nautilus-emission-v1, Nautilus=1.230.0 all validated. |
| **§1 TRAIN fence & UTC fence** | `source.py:112-126` `_validate_utc_fence`; `source.py:168` | MATCHES | `train_end_ns` (1_700_611_200 * 1_000_000_000) validated against `train_end_utc` "2023-11-22T00:00:00Z". |
| **§1 Composite ID uniqueness** | `source.py:129-152` `_validate_composite_uniqueness`; `source.py:319-337` | MATCHES | `(source_cell, raid_id)` uniqueness checked across all 264 cells. |
| **§1 Causal timestamp provenance** | `source.py:275-297` | MATCHES | `raid_ts_ns ≤ sweep_ts_ns ≤ return_ts_ns ≤ confirmation_ts_ns ≤ endpoint_ts_ns` validated per cell. |
| **§1 Schema/object/count reconciliation** | `source.py:234-268` | MATCHES | Required columns present; row counts match metadata; `source_configuration == config`; no rows after TRAIN fence. |
| **§1 Binding ATR_UNDEFINED exclusion** | `adapter.py:205-215` `_channel_frame` | MATCHES | `swing_atr` and `strong_move` exclude rows where `profile_undefined_reason == "ATR_UNDEFINED"`. |
| **§2 Mechanism, causal regime, object identity** | `design.md:47-67`; `analysis.py:126-135` `contrasts`; `analysis.py:136-142` `stratum_columns` | MATCHES | Causal WilderATR(14) updates on completed observation bars; `x_t = ATR_t / close_t`; regime from post-update ranking; raid/confirmation/endpoint regimes tied to event timestamps. |
| **§2 Regime provenance & preceding-mark join** | `analysis.py:205-280` `live_frame`; `analysis.py:30-85` `frequency_rate` | MATCHES | Raid `sweep_ts_ns` joined to preceding completed observation mark's `causal_regime`; `bar_marks.regime` is post-update label; `VOID_REGIME_PROVENANCE` if mismatch. Warmup/undefined retained. |
| **§3 Population & estimands** | `analysis.py:134-142` `_channel_frame`; `analysis.py:126-135` `contrasts` | MATCHES | Primary population = COMPLETED & primary_attribution & primary_completed; fixed comparator = MID regime; LOW/HIGH vs MID contrasts. |
| **§3 Raid-frequency estimand** | `analysis.py:30-85` `frequency_rate`; `analysis.py:185-200` `frequency_bootstrap` | MATCHES | Exposure = preceding marks with LOW/MID/HIGH regime; starts = raids with matching regime; rate = 1000 * starts/exposure; contrast = rate - rate_MID. Block lengths 12, 24, 48, 96, 192 (15m/30m/1h one-day + half/double). |
| **§3 Primary outcome estimators** | `analysis.py:126-135` `contrasts`; `adapter.py:127-130` `control_channels` | MATCHES | Mean `swing_atr`, mean `swing_duration_ns`, unpaired `strong_move` proportion difference. |
| **§4 Joint cluster bootstrap (outcomes)** | `statistics.py:80-160` default `independent_arms=False` | MATCHES | Level clusters resampled jointly (level may contribute LOW/MID/HIGH); circular block bootstrap, L=2/5/10, 5 seeds, 10k draws. |
| **§4 Frequency bootstrap** | `analysis.py:87-120` `_frequency_bootstrap_units` | MATCHES | Resamples chronological observation-mark units carrying raid-start lists; block lengths per timeframe. |
| **§4 Empty arm/exposure handling** | `statistics.py:203-214`; `analysis.py:40-45` | MATCHES | Returns `EMPTY_ARM`/`EMPTY_EXPOSURE` with counts, null estimate/interval; row not removed. |
| **§4 Report layers** | `adapter.py:489-502` | MATCHES | Observed/ideal/interpretation/analyst_boundary fields; no prohibited value labels. |
| **§5 Cross-regime future destroy grouping** | `destroy.py:230-256` `stream_destroy_control` | MATCHES | Groups by `archive_symbol × timeframe × confirmation_method × confirmation_reference × config × side × status × primary_completed × 5-bit nullness class`; regime labels pooled. |
| **§5 Derangement (zero fixed points)** | `destroy.py:72-85` `derange_indices`; `destroy.py:241-246` | MATCHES | Rejection sampling until `perm[i] != i`; singleton groups VOIDed. |
| **§5 Exact nested 10k×2k destroy** | `destroy.py:507-532` `compute_exact_nested_destroy_se` | **MISSING** | Placeholder (`pass`). Design requires per-bootstrap-population destroy recomputation. Current implementation uses average-then-bootstrap + hypot. |
| **§5 Fixture topology & plants** | `adapter.py:77-116` `make_fixture_frame` | DEVIATES | Design specifies 200 rows/arm (MID/HIGH) with explicit plants (+0.50 ATR, +3.6e12 ns, +0.25 proportion). Shared fixture uses gradient across configs. |
| **§5 Nullness class: `duration_ns` vs `swing_duration_ns`** | `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns` | DEVIATES | Design declares `duration_ns` as the nullness bit alias. Code uses canonical `swing_duration_ns`. |
| **§6 Sample size & complexity** | `design.md:164-177`; `adapter.py` | MATCHES | No minimum n; all rows retained; channels with sigma_denominator; frequency audit separate. |
| **§6 Hard/informative split** | `design.md:179-186`; `contract.py` `IntegrityStatus` | MATCHES | Hard blocks: gate-first, fence, causality, schema, no-local-accounting, deterministic, ATR exclusion, future-destroy validity, frequency exposure-denominator validity, zero-cost. Informative: operator judges all effects. |
| **§7 Golden trace** | `design.md:182-195` | MATCHES | T1: pre-update LOW regime; T2: post-update HIGH regime for bar_marks; T3: same-timestamp reference consumes post-update confirmation_regime=MID; endpoint_regime=MID. |
| **§8 Amendment ledger & final null** | `design.md:198-245` | MATCHES | 2L/3T/8N; no machine qualifier; no row hiding; F02/F04/F06 N/A; F07 satisfied. |
| **§9 Zero-cost disclosure** | `contract.py:10-25` `ZERO_COST_DISCLOSURE` | MATCHES | Canonical text verbatim; `NO_COST_CHARGED`; no prohibited claims. |
| **Failed-control propagation** | `adapter.py:426-431` | MATCHES | Failed control reasons collected into overall integrity reasons. |
| **Live orchestration & integrity gating** | `runtime.py:75-99` `_execute`; `analysis.py:233-238` | MATCHES | `--live` runs `run_live` → `adapter.integrity` → blocks `analyze` if integrity fails → atomic write. |
| **§3 Frequency blocks (12,24,48,96,192)** | `analysis.py:26-28` `FREQUENCY_BLOCK_LENGTHS` | MATCHES | All five block lengths implemented for 15m/30m/1h one-day + half/double. |
| **§3 Warmup/undefined retained** | `analysis.py:205-280` `live_frame` | MATCHES | `REGIME_WARMUP` and `ATR_UNDEFINED` exposure reported separately; never converted to arm. |
| **§3 EXP-100 gate** | `analysis.py:205-280` `live_frame` | MATCHES | Uses EXP-100 `estimand_validation.json` (local copy byte-identical) as gate. |
| **§3 Causal preceding-mark** | `analysis.py:205-280` `regime_source_ts_ns` join | MATCHES | Raid `sweep_ts_ns` joined to preceding completed observation mark's regime; `VOID_REGIME_PROVENANCE` on mismatch. |

### Golden-trace diff

| Event | Expected from design | Implemented logic | Verdict |
|---|---|---|---|
| T1 pre-update LOW | cached x=0.80, lower=0.90, upper=1.10 → LOW | `bar_marks.regime` post-update; raid regime pre-update | MATCHES |
| T2 post-update HIGH | x=1.20 appended, window bounds unchanged → HIGH | `bar_marks.regime` authoritative post-update label | MATCHES |
| T3 same-timestamp MID | 11:00 observation update processed before reference → MID | Causal join to preceding mark; post-update state consumed | MATCHES |
| Fixture plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion | Shared fixture gradient across configs | DEVIATES |
| Nested destroy | Per-outer-population recompute | Average-then-bootstrap + hypot | **DEVIATES** |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no implementation authorship in this context.
- **Gate-first:** PASS — `validate_source_contract` checks family gate (264 cells) before any parquet read.
- **TRAIN/holdout:** PASS — `train_end_ns` fence enforced; no TEST/holdout paths in code.
- **Registry:** PASS — `CF-LIQSWP-001/HYP-004` registered; 0 candidate slots; 0 counted TEST reads.
- **No Python backtest/local accounting:** PASS — `check_no_local_accounting` would pass; no accounting primitives.
- **One BacktestNode:** PASS — EXP-104 is analysis-only; EXP-100 metadata attests `one_backtest_node=true`.
- **Derangement:** PASS — `derange_indices` uses rejection sampling; `VOID_FIXED_POINTS` if any.
- **Zero cost:** PASS — Canonical disclosure verbatim; `NO_COST_CHARGED` in all metadata.
- **No research powering:** PASS — No MDE, power curves, `UNPOWERED`, detection floors.
- **PSR:** N/A — No trade/leg bps series.
- **Screen conversion/XENA:** N/A.
- **Battery rules:** PASS — No adaptive selection, capped read, exit selection, or phase-shift gate.

### Issues

1. **HIGH — Exact nested 10k×2k destroy not implemented.**
   **Design:** §5 "outer bootstrap: for each seed s=0..4, generate 10,000 cluster-bootstrap populations... For every population b, recompute the raw contrast D_raw[s,b] AND all 2,000 deranged contrasts D_destroy[s,b,d]."
   **Code:** `destroy.py:507-532` `compute_exact_nested_destroy_se` is a placeholder (`pass`). `adapter.py:323-378` computes destroy contrasts only once on the original population, then bootstraps the *average* destroyed values.
   **Required change:** Implement the exact nested destroy per bootstrap population.
   **Failing artifact:** `python/src/xen/liqswp_analysis/destroy.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

2. **HIGH — Fixture plants deviate from design specification.**
   **Design:** §5 FIXTURE-TOPOLOGY specifies 200 rows per arm (MID/HIGH) with explicit plants.
   **Code:** `adapter.py:77-116` `make_fixture_frame` uses shared `make_fixture_frame` with gradient values.
   **Required change:** Implement dedicated two-arm fixture matching design's explicit plants.
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `quant-designer` or `experiment-developer`.

3. **MEDIUM — Nullness class uses `swing_duration_ns` instead of declared `duration_ns`.**
   **Design:** §5 nullness class tuple includes `is_null(duration_ns)`.
   **Code:** `analysis.py:50-55` `CONTROL_NULL_COLUMNS` uses `swing_duration_ns`.
   **Required change:** Use `duration_ns` in nullness class for traceability.
   **Failing artifact:** `python/experiments/EXP-104/analysis_code/analysis.py`, `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

4. **MEDIUM — Missing `swing_price`/`swing_bps` source-field summaries in analysis output.**
   **Design:** §4 "Raw `swing_price` and `swing_bps` are source-field summaries."
   **Code:** `adapter.py:489-502` does not include raw mean/summary for these channels.
   **Required change:** Add source-field summaries to output.
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

5. **LOW — Empirical 95% destroyed interval missing from live control disclosure.**
   **Design:** §5 "disclosure: ... empirical 95% interval".
   **Code:** Live control path uses `destroyed_outer_se` (hypot), not empirical quantiles from 2,000 destroyed contrasts.
   **Required change:** Include empirical 95% interval from destroyed contrasts in live records.
   **Failing artifact:** `python/src/xen/liqswp_analysis/adapter.py`. **Required skill:** `experiment-developer`.

### Summary

**REVISE.** EXP-104 correctly implements frequency blocks (12,24,48,96,192), warmup/undefined retention, EXP-100 gate, causal preceding-mark provenance with `VOID_REGIME_PROVENANCE`, joint cluster bootstrap, frequency bootstrap, derangement-based cross-regime destroy, singleton VOID, UTC fence + composite ID, failed-control propagation, and neutral report layers. The golden trace matches the frozen regime logic.

The critical **HIGH** issue shared across all experiments: exact nested 10k×2k destroy is not implemented (average-then-bootstrap+hypot used instead). Additional **HIGH/MEDIUM** issues: fixture plant deviation, nullness class field name mismatch, missing source-field summaries, missing empirical destroyed interval. Route to `experiment-developer` for implementation fixes and `quant-designer` for fixture design alignment.


## QA run 8 — 2026-08-17T23:50:23Z — mode: subagent — HEAD 62983d0cf0136b7caf1ec2aea8c41d3b92abdec1

Reviewed git state: working tree clean; `git rev-parse HEAD` = 62983d0; the last commit touching experiment code is `e57847c` ("fix(EXP-101-104): implement exact nested destroy and registered fixture plants").
Scope: verify the run-7 (HEAD 8127c23) REVISE findings are resolved and no new issues are introduced. Fresh-context review; no implementation/design/test/receipt file was modified. No live analysis, engine, TEST, or holdout access; EXP-100 retained as read-only source (its gate was read first).

Verdict: **REVISE**

The five run-7 REVISE items and the AMENDMENT-15 contract are correctly resolved in code and receipt. Two MEDIUM design-to-code gaps remain in the frequency-leg live report (§3): sensitivity block lengths are not dispatched per timeframe (only {24,48,96} run for every stratum; 12 and 192 never orchestrated), and the live frequency census omits the observed rates/contrasts and the separately-required warmup/undefined exposure counts. Both are informative-disclosure fixes before execution.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §5 TRIPWIRE live read — AMENDMENT-15 acceptance inequality per seed | `destroy.py:657-699` `future_destroy_attestation` | MATCHES | For each seed with finite raw stats and `abs(D_raw) > INTEGRITY_Z*bootstrap_SE_raw[s]`, requires `abs(m_destroy) <= INTEGRITY_Z*bootstrap_SE_raw[s]`; violation adds `VOID_FUTURE_DESTROY_SURVIVAL` and blocks. Principle uses the live empirical 2,000-draw destroyed mean (`finite_destroyed`), raw SE from the nested bootstrap; `destroyed_survives_threshold` string matches AMENDMENT-15. |
| §5 AMENDMENT-15 — bootstrap_SE_mean_destroyed still computed/disclosed per seed | `destroy.py:647-697`; `adapter.py:379-400` | MATCHES | `nested_seeds` per control record carry `bootstrap_se_raw` and `bootstrap_se_mean_destroyed` per seed 0..4 (verified in `fixture_integrity.json` for all 6 records). |
| §5 closed-form nested destroy (10k × 2k per seed) | `destroy.py:538-646` `nested_destroy_bootstrap`; `_destroy_draw` `destroy.py:644-727` | MATCHES | Per outer population b, m_destroy[b] = Σ_g (W_g·G_g − S_g)/(m_g−1) for m_g≥2 else S_g, on b's own rows via per-cluster per-group sufficient statistics (A/SA/SAQ/C/SC/SCQ); within-population derangement expectation/variance formulas independently re-derived and verified against exact derangement enumeration (see below). SE = sqrt(var_between + mean_b(Var_draw)/n_destroy); both components disclosed. |
| §5 outer-bootstrap mechanics (joint cluster resampling, L=5 primary seeds 0..4, 10k) | `destroy.py:563-645`; `statistics.py:76-101` `circular_cluster_indices` | MATCHES | Circular whole-cluster blocks, cap L at n_clusters−1, `ceil(n/effective)` starts drawn from [0,n), truncate to n; same default_rng(seed) stream order as `clustered_contrast_bootstrap` (integer-draw count per population matches), so bootstrap_SE_raw is comparable to the raw bootstrap intervals disclosed in control records. |
| §5 live donor derangement draws (2,000 seeds, zero fixed points, full donor pool, all regimes pooled) | `destroy.py:319-401` `draw_destroy_contrasts`; `derange_indices` `destroy.py:85-92` | MATCHES | Groups on exact stratum × status × primary_completed × 5-bit nullness (regime labels pooled within group; per-group derangements, rejection sampling, fixed_points=0); non-arm/comparator rows remain in the group as donors (config-pooled donor). Empirically verified against the seeded reference mapping in `test_destroy.py`. |
| §5 non-vacuity / VOID handling | `destroy.py:352-400`; `future_destroy_attestation` | MATCHES | VOID_SINGLETON_GROUP, VOID_NO_MOVABLE_ROWS, VOID_NO_CHANGED_VALUE, VOID_POPULATION_MISMATCH, VOID_NONFINITE_* reasons block; empty-arm returns EMPTY_ARM_OR_COMPARATOR note with pass (disclosed). Minor edge: an empty-arm early return carries reasons but sets `blocking_pass=True` (see issue F4). |
| §5 fixture plants and topology | `adapter.py:88-160` `make_fixture_frame`; EXP-104 `Adapter.fixture_frame` | MATCHES (with note) | +0.50 ATR (MID 0.90/1.10, arms 1.40/1.60), +3.6e12 ns duration, +0.25 strong_move (1/4 vs 1/2); 200 rows/arm, deterministic permutation seed 4, ordering (first_raid_timestamp, level_id), first_raid_timestamp = 1.7e18 + i·9e11; both (MID,LOW) and (MID,HIGH) contrasts planted. Note (F5): MID rows repeat `FIXTURE-MID-level-####` across the two pairs, so MID level clusters hold two identical rows (statistically equivalent to cluster_size=1, literal topology differs). |
| §5 every-seed/every-channel fixture must pass, blocks live control | `results/fixture_integrity.json` (regenerated, receipt mtime 2026-08-17 12:26) | MATCHES | 6 control records (2 arms × 3 channels), all `blocking_pass=true`, empty reasons, `raw_bite=true` with seeds [0,1,2,3,4], `destroyed_survives=false`, 2,000 destroyed contrasts, empirical `destroyed_interval`, `nested_seeds` per record. Production `run_fixture(n_boot=10)` reproduces the receipt byte-for-byte (verified). |
| §8 amendment ledger / final null accounting | `design.md:347-406` (AMENDMENT-15 at 402-406) | MATCHES | 3 looser / 3 tighter / 8 neutral running count; A-15 declared LOOSER; no ≥3 one-directional streak (tightest run is A6/A7 = 2); zero expected machine false-qualifiers by construction. |
| §2/§7 golden-trace regime causality | `exp100/processor.py:114-126,285-350,462-498`; `features.py:151-185` | MATCHES | Raid/excursion read `_last_regime` (pre-update cached state) before `_on_observation_bar`; regime appends the current value before ranking with linear (n−1)·0.33/(n−1)·0.67 bounds and strict tie rules; reference events processed after the observation update, so same-timestamp confirmation/endpoint consume post-update MID. |
| §3 raid-frequency estimand (exposure/starts/rates/contrasts) | `analysis.py:83-129` `_frequency_from_units`/`frequency_rate` | PARTIAL | Core estimator correct (preceding-mark exposure, unique raid starts per bar, rate=1000·starts/exposure, LOW/HIGH-minus-MID, empty-exposure lists, warmup/undefined listed in the fixture-facing path). However the **live** census (`analysis.py:296-322`) emits only exposure/starts counts — observed rates and contrasts, and warmup/undefined exposure counts, are not in the live output (F2). |
| §3 frequency uncertainty — one-day blocks L=96/48/24 with sensitivities L/2 and 2L | `analysis.py:48-49,330-336` | DEVIATES | `FREQUENCY_BLOCK_LENGTHS=(12,24,48,96,192)` is defined but never used; the live loop runs `FREQUENCY_BLOCK_LENGTHS_DEFAULT=(24,48,96)` identically for every stratum/timeframe. Per design, 15m cells need {48,96,192}, 30m {24,48,96}, 1h {12,24,48}; 192 and 12 are never orchestrated (F1). |
| §4 outcome estimator, joint bootstrap, L=2/5/10, seeds | `statistics.py:157-270`; `adapter.py:462-520` | MATCHES | Joint cluster resampling, L=5 primary with L=2/L=10 sensitivities, 10k draws, 5 seeds, linear percentiles, finite-draw counting (NaN draws excluded with counts — run-5 issue resolved), EMPTY_ARM/ONE_CLUSTER reasons retained. |
| §4 secondary summaries — swing_price/swing_bps | `adapter.py:474-500` | MATCHES | `source_field_summaries` arm/comparator n, non_null, mean, median for both channels in every value row (run-7 issue resolved). |
| §5 nullness class uses `duration_ns` alias | `adapter.py:39-44`; `analysis.py:56-64`; alias assertion `adapter.py:284-298` | MATCHES | 5-bit tuple (swing_price, swing_bps, swing_atr, duration_ns, strong_move); `duration_alias_nullness_mismatch` and `duration_alias_mismatches` asserted in `integrity()` (run-7 issue resolved). |
| §5 empirical 95% destroyed interval in control records | `destroy.py:692-694`; receipt records | MATCHES | `destroyed_interval` = [q0.025, q0.975] of the 2,000 destroyed contrasts per control record (run-7 issue resolved). |
| §5 non-bite threshold is raw SE (AMENDMENT-15), not destroyed SE | `destroy.py:671-682` | MATCHES | Verified in receipt: destroyed means (−6.2e−4 ATR, −4.6e9 ns, −1.8e−3 strong) are inside ±2.8·bootstrap_se_raw (0.0125 ATR at 10k scale) for every seed/channel. |
| §1 gate-first / frozen source / UTC fence / composite ID | `source.py:180-345`; repair diff `e57847c` | MATCHES | Family gate (264 cells) checked before any parquet read; fence receipts validate `train_end_utc` when present and `train_end_ns` when present; object-id uniqueness cell-scoped with composite (source_cell, raid_id) check; EXP-100 vs EXP-104 gate copies byte-identical (SHA256 1593851873…). Issues F3 (default gate path) noted. |
| §1 no source mutation / analysis-only | `analysis_code/analysis.py`; `runtime.py` | MATCHES | Reads only; atomic result write; no strategy, order, engine, or holdout path. |
| No-order/PSR, no cost, no powering | design §§6/9; code scan | MATCHES | PSR declared N/A (no trade/leg-bps estimand); `ZERO_COST_DISCLOSURE` verbatim (contract test asserts equality); no cost-function import (`PARTIAL_FEES`, `spread_scale_route`, `bybit_round_trip_cost_bps` absent); INTEGRITY_Z=2.8 is the only scale constant and is validity-only. |

### Golden-trace diff

| Event | Expected (from design) | Implemented logic | Verdict |
|---|---|---|---|
| T1 (10:00, pre-update) | Cached x=0.80 below lower=0.90 → raid/excursion regime LOW before the current observation update | `processor.py:285-293` captures `atr`/`regime = self._last_regime` before `_on_observation_bar`; `_on_reference_bar` unchanged afterwards | MATCHES |
| T2 (10:15, post-update) | x=1.20 appended before ranking; retained 252-window bounds 0.90/1.10 → bar_marks.regime HIGH; equality would be MID | `features.py:151-165` appends then ranks with strict `<`/`>` comparisons; bar mark emitted post-update | MATCHES |
| T3 (11:00 observation + reference) | Observation x=1.00 updates to MID before the same-timestamp reference → confirmation_regime=MID (not HIGH); endpoint stays MID through 12:00; original raid LOW unchanged | `processor.py:114-126` observation processed before reference; confirmation/endpoint read `self._last_regime` (post-update); raid fields never rewritten | MATCHES |
| Fixture plants | +0.50 ATR, +3.6e12 ns, +0.25 proportion; destroyed non-bite vs raw SE for every seed/channel | `make_fixture_frame`; receipt shows raw=0.5/3.6e12/0.25, raw-bite seeds [0..4], destroyed non-bite for all 6 records | MATCHES |
| Nested destroy | Closed-form mean/variance of the 2,000-draw destroyed contrast inside every resampled population b | `_derangement_variance` and expectation `(W·G−S)/(m−1)` verified this run against exact derangement enumeration for 2 groups (m=3..6 and arbitrary weights); unit test covers m=2..6 | MATCHES |
| Frequency uncertainty set | Per-timeframe L/2, L, 2L (192 for 15m, 12 for 1h) | Live loop runs {24,48,96} for all strata; 12/192 unreachable | DEVIATES |

### Governance & boundary

- **Fresh context:** PASS — dedicated subagent; no authorship of the reviewed implementation in this context.
- **Gate-first:** PASS — `validate_source_contract` checks the family gate (blocking_pass, 264 cells) before cell scans; per-cell gates cross-checked (config_hash, no_cost ok, blocking_pass).
- **TRAIN/holdout fence:** PASS — `train_end_ns = 1_700_611_200·1e9` = 2023-11-22T00:00:00Z (recomputed); `scan_train_columns` filters rows after the fence; no TEST/holdout path.
- **Registry preconditions:** PASS — `CF-LIQSWP-001/HYP-004` registered (multiplicity-registry.md:1724), 0 counted TEST reads, family REGISTERED.
- **Zero-cost verbatim:** PASS — receipt `zero_cost_disclosure` equals `contract.py ZERO_COST_DISCLOSURE`; no cost function on any live path; no prohibited claims.
- **No research powering:** PASS — no MDE, MDE_Z, power curve, detection floor, `UNPOWERED`, `min_powered_seeds`, `n_legs_floor` in EXP-104 code/design; INTEGRITY_Z=2.8 appears only in the tripwire validity check.
- **No local accounting:** PASS — `check_no_local_accounting("python/experiments/EXP-104/analysis_code")` → `{'ok': True, 'banned_defs_found': []}`.
- **Derangement:** PASS — zero fixed points by rejection sampling; VOID on singleton/no-change groups; test coverage present.
- **One BacktestNode:** PASS — analysis-only; no BacktestNode, no engine process, in EXP-104 code.
- **PSR:** N/A — no trade/leg-bps or Sharpe series; design declares PSR N/A.
- **XENA / conversion pin / battery rules:** N/A — no XENA route, no SPDR/screen money conversion, no battery/capped-read gate; F02/F04/F06 declared N/A, F07 satisfied.
- **Amendment ledger:** PASS — 3 looser / 3 tighter / 8 neutral; no streak ≥3; final-null accounting statement present.
- **Bounded runtime proof:** PASS — `test_exp10x_nested_destroy_performance.py` at registered live scale (5 seeds × 10k outer × 2k destroys on 4,000 rows / 1,000 clusters): 4.58s joint, 2.33s independent (bound 120s); fixture stratum at live scale completes in ~1.4s.
- **Tests run:** `pytest python/tests/liqswp_analysis python/tests/test_exp10x_analysis_contract.py python/tests/test_exp10x_nested_destroy_performance.py -q` → 49 passed; `pytest test_exp101/102/103_analysis_live.py -q` → 16 passed (shared source-contract path against the real EXP-100 source, exercising the source.py repairs).

### Issues

1. **MEDIUM — frequency sensitivity block lengths are not dispatched per timeframe (design §3 DEVIATES).**
   `analysis.py:48-49` defines `FREQUENCY_BLOCK_LENGTHS=(12,24,48,96,192)` but it is never referenced; the live orchestration (`analysis.py:330-336`) runs the same `(24,48,96)` for every stratum regardless of timeframe. The design requires, per cell: 15m → L=96 with sensitivities 48 (=L/2) and **192 (=2L)**; 30m → 24/48/96; 1h → L=24 with sensitivities **12 (=L/2)** and 48. Lengths 12 and 192 are therefore never produced. (The RNG/mechanics themselves are exact.)
   **Required change:** dispatch block lengths per observation timeframe in the live frequency-uncertainty loop so each cell emits {L/2, L, 2L} with L∈{96,48,24}, e.g. use `FREQUENCY_BLOCK_LENGTHS` per the partition's `timeframe`.
   `Failing artifact: python/experiments/EXP-104/analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

2. **MEDIUM — live frequency census omits the registered observed layers (design §3 DEVATES).**
   The live census (`analysis.py:296-322` `frequency_rows`) emits only per-regime `exposure` and `starts` counts. The design defines `rate_r = 1,000·starts_r/exposure_r` and `contrast_r = rate_r − rate_MID` as the estimand and the REPORT-LAYERS §4 list observed "rates ... direct contrasts" (and design §3 requires warmup/undefined exposure "reported separately"). The fixture-path `_frequency_from_units` computes these, but the live branch never calls it for the observed row and never counts warmup/undefined EXPOSURE marks (`marked_exposure` at `analysis.py:280-281` filters to LOW/MID/HIGH only). The uncertainty section reports only bootstrap intervals.
   **Required change:** emit the observed rate/contrast plus warmup/undefined exposure counts per stratum in the live census (reuse `_frequency_from_units` on the stratum's units), while keeping exposure/start counts.
   `Failing artifact: python/experiments/EXP-104/analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

3. **LOW — CLI live default gate points at the EXP-104 local copy, not the EXP-100 authority (design §1).**
   `analysis.py:439` defaults `--gate` to `experiment_root/"results/estimand_validation.json"` (EXP-104 copy). The copy is byte-identical to EXP-100's today (SHA256 1593851873…), and `validate_source_contract` cross-checks family vs per-cell gates, so a drift would be caught; but the pinned authority in design §1 is `python/experiments/EXP-100/results/estimand_validation.json`.
   **Required change:** default to the authoritative EXP-100 gate path (as EXP-102 does), or add an explicit guard that the file is byte-identical to the authoritative gate.
   `Failing artifact: python/experiments/EXP-104/analysis_code/analysis.py`; `REQUIRED_SKILL: experiment-developer`.

4. **LOW — empty-arm early return keeps blocking_pass=True even when VOID reasons exist.**
   `destroy.py:612-629` returns `blocking_pass=True` for an EMPTY_ARM_OR_COMPARATOR population while passing through any collected `VOID_SINGLETON_GROUP`/`VOID_NO_MOVABLE_ROWS` reasons. Because an empty arm already makes the row uninterpretable (EMPTY_ARM disclosed), this is acceptable in effect, but it means a control record can carry a VOID reason with pass=true.
   **Required change (optional):** in the empty-arm branch, drop or explicitly annotate non-applicable destroy reasons, or document the pass-with-reasons semantics in the receipt schema.
   `Failing artifact: python/src/xen/liqswp_analysis/destroy.py`; `REQUIRED_SKILL: experiment-developer`.

5. **LOW (informational) — fixture MID clusters are duplicated across the two baseline pairs.**
   `adapter.py:88-160`: pairs (MID,LOW) and (MID,HIGH) both emit 200 MID rows with level_id `FIXTURE-MID-level-####`, so `FIXTURE-TOPOLOGY`'s "one row is one complete level cluster" holds for LOW/HIGH but not MID (200 two-row identical clusters). Statistically equivalent (identical rows), including the receipt's single 800-row destroy group and raw estimates.
   **Required change (optional):** reserve distinct MID level ids per pair (e.g. `level-{pair}-{i:04d}`) for literal topology fidelity.
   `Failing artifact: python/src/xen/liqswp_analysis/adapter.py`; `REQUIRED_SKILL: experiment-developer`.

6. **Coverage gap (not a design breach) — no EXP-104 live-path test.**
   There is no `python/tests/test_exp104_analysis_live.py`; EXP-101/102/103 each have one. EXP-104's live path (its `live_frame` profile-key joins, `VOID_PROFILE_JOIN_MISMATCH`, `VOID_REGIME_PROVENANCE`, per-cell mark scans, and frequency-census orchestration) is only covered indirectly — the shared `validate_source_contract` is exercised by the other experiments' live tests against the real EXP-100 source, and EXP-104 fixture behavior is covered by `test_exp104_adapter.py` + the parametrized `test_exp10x_analysis_contract.py`. Live-path coverage exists but is not EXP-104-specific.
   **Recommended change:** add a `test_exp104_analysis_live.py` mirroring EXP-103's (gate-first on the retained source + a fixture regression for the EXP-104 control), which also asserts the §3 frequency census fields (see issues 1-2).
   `Failing artifact: python/tests/`; `REQUIRED_SKILL: experiment-developer`.

### Run-7 items verified as resolved

1. Exact nested 10k×2k destroy — **resolved** (`nested_destroy_bootstrap` closed-form; math independently re-derived and matched against exact derangement enumeration; 2,000-draw live read kept; performance proof 4.58s/2.33s).
2. Registered fixture plants — **resolved** (two-arm +0.50 ATR / +3.6e12 ns / +0.25 strong_move; receipt regenerated and passing, 6/6 control records).
3. Nullness class `duration_ns` alias — **resolved** (5-bit class uses `duration_ns`; alias equality asserted).
4. swing_price/swing_bps source summaries — **resolved** (`source_field_summaries` in every value row).
5. Empirical 95% destroyed interval — **resolved** (`destroyed_interval` per control record).

### Independent checks run (this review)

```text
git rev-parse HEAD / status: clean at 62983d0
pytest python/tests/liqswp_analysis python/tests/test_exp10x_analysis_contract.py \
      python/tests/test_exp10x_nested_destroy_performance.py -q          -> 49 passed
pytest test_exp101/102/103_analysis_live.py -q                            -> 16 passed
check_no_local_accounting(python/experiments/EXP-104/analysis_code)      -> {'ok': True, 'banned_defs_found': []}
closed-form destroy (sum of (W·G−S)/(m−1) per group) vs exact derangement enumeration -> equal (2 groups, m=3)
fixture receipt: 6 control records, all blocking_pass, 2000 destroyed contrasts each, nested seeds 0..4
live-scale nested run on fixture stratum (10k outer): ~1.4s, destroyed non-bite holds (0.00062 <= 2.8·0.00446)
TRAIN fence recompute: 1700611200 s == 2023-11-22T00:00:00Z
gate byte-identity: EXP-100 vs EXP-104 estimand_validation.json SHA256 1593851873…
```

### Residual risks

- The two MEDIUM frequency-report gaps (issues 1-2) affect only the informative frequency leg and its disclosure; the hard/validity layer is clean.
- The nested closed form follows the "same per-population donor pool" reading of §4/§5 (cluster resamples carry the arm/comparator rows of each contrast); the live donor additionally pools all regime rows per §5. The two populations are identical in row set only for two-regime strata; residual nuance is disclosed in the docstring.
- No live execution artifact exists yet (`results/analysis_results.json` absent) — this remains the operator's gate.

