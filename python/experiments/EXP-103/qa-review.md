## QA run 1 — 2026-08-11T03:52:39Z — mode: subagent — HEAD d9730b5982c8d4b4e2ed76f2f458d87e2ee70a03

Verdict: REVISE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Liquidity-level catalogue includes previous 1D/1W/4H/1H levels | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:6,56`; checkpoint `design.md:104` | DEVIATES | Checkpoint excludes 1W. |
| Sweep causal ordering and raid state | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:10-22`; checkpoint `design.md:131-153` | MATCHES | Strict excursion, inclusive return, ambiguity, ordering, and positive reversal are stated. |
| Value-gap interval and profile definition | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:43-49,67`; checkpoint `design.md:158-181` | MATCHES | Includes the strict rule `gap_span < 0.30*(VAH-VAL)`. |
| Timeframes, confirmation references, sessions, ATR, 1m input, fences and holdout | checkpoint `design.md:75-121,141-153,305-307` | MATCHES | 1H references are used for 15m/30m and 1D for 1h. |
| Controls and required emissions | checkpoint `design.md:204-253`; EXP-103 `design.md:46-55` | MATCHES | Design-only review; no implementation exists. |

### Golden-trace diff

No implementation or smoke emission exists. The design-only golden trace is consistent for the matched clauses; the 1W catalogue branch is an explicit deviation.

### Governance & boundary

- Review mode: fresh `subagent` context.
- No experiment was run and no implementation was reviewed.
- Reviewed state: 5 modified files and 11 untracked paths at the reviewer timestamp.
- Literal 100% SoT preservation is not established.

### Issues

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 2 — 2026-08-13T18:16:59Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75

Verdict: REVISE

### Review scope and implementation status

This is a design/readiness review of EXP-103 only, against its current design, checkpoint `2026-08-11-019-liquidity-sweeps`, registered family `CF-LIQSWP-001`, and shared pipeline/governance rules. The EXP-103 directory contains only `design.md` and `qa-review.md`; no EXP-103 `code/`, runner, emission, `analysis_code/`, or results artifact exists. The requested frozen EXP-100 AMENDMENT-13 TRAIN emission is therefore treated as the intended source, not as a new run. No Nautilus process was launched and no TEST, holdout, or future data was loaded or inspected.

### Reviewed git state

Dirty files before this append:

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

### Design-fidelity trace

`N/A — no EXP-103 implementation` in the code column is intentional. It means runtime fidelity cannot be proven; it does not invent a code location.

| Design clause (§ref) | Code / frozen-source location | Verdict | Notes |
|---|---|---|---|
| Family, universe, TRAIN scope, 264 cells, and AMENDMENT-2 through AMENDMENT-13 (`design.md:3-15`) | No EXP-103 code. Checkpoint `design.md:147-177`; family contract `cf-liqswp-001.md:3-8,20-47`; universe pin | MATCHES (design-level) | cTrader-only instruments, 1W catalogue, 1H/4H confirmation pairing, rolling 7/14/22/252, and final count 2L/3T/7N agree. The prior QA run's 1W deviation is resolved in the current sources. |
| Mechanism and derived estimand (`design.md:17-27`) | No EXP-103 code. Checkpoint `design.md:110-127,263-277` | MATCHES (design-level) | Tight-gap versus non-tight defined-profile outcomes and the future-destroyed post-confirmation null are aligned. The frozen source artifact is not identified. |
| Object identity and non-overlapping windows (`design.md:29-39`) | No EXP-103 code. Checkpoint `design.md:129-141,201-228` | DEVIATES | AMENDMENT-6 leaves only the latest primary-attributed confirmed raid live for the later swing; EXP-103's control/comparator population says only “completed raids with defined profiles” and does not define the primary-outcome eligibility mask or profile-only non-primary arm. |
| Frozen online TPO profile algorithm (`design.md:41-63`) | No EXP-103 code. Checkpoint `design.md:230-261`; family `cf-liqswp-001.md:87-107` | MATCHES (text; implementation missing) | Source bars, reset point, bin width, TPO contribution, POC, VA, 30% selection, exact mask, and strict 50% tightness agree. No emitted-column or frozen-run mapping exists. |
| Required checks and profile/output contract (`design.md:65-71`) | No EXP-103 code or smoke emission. Checkpoint `design.md:314-331` | MISSING | The checks are listed, but EXP-103 does not name the frozen EXP-100 aggregate fields needed to perform them, including the exact mask, VA/TPO counts, gap span ratios, reason codes, primary attribution, and outcome availability. |
| Future-destroy control and tripwire (`design.md:73-91`) | No EXP-103 code. Checkpoint `design.md:279-312`; requirements §3-4 | DEVIATES | The design declares a derangement and zero fixed points, but does not explicitly state disjoint alignment from the raw outcome series. Runtime regeneration/rejection of fixed points and the declared non-vacuity bite cannot be verified without code. |
| Operator-only bands and fixed comparator (`design.md:93-106`) | No EXP-103 code. Checkpoint `design.md:333-355` | MATCHES (design-level) | Per-stratum non-tight comparator, all-profile baseline, no count gate, visible thin rows, and no research-power machinery are aligned. The bands remain labels, not machine fields. |
| Golden trace (`design.md:108-117`) | No EXP-103 code or smoke emission. Checkpoint `design.md:357-379` | DEVIATES | The arithmetic labels are stated, but no timestamped input bars, ATR/bin grid, TPO counts, POC/VA expansion, selected mask, or boundary event is provided, so QA cannot hand-rederive the expected mask and span. |
| Hard/informative split (`design.md:119-126`) | No EXP-103 code. Checkpoint `design.md:381-389` | MATCHES (design-level) | Integrity is separated from value reads and no machine value verdict is declared. No-local-accounting and estimand-validation evidence remain unavailable because no analysis path exists. |
| Zero-cost disclosure (`design.md:128-142`) | No EXP-103 live path. Checkpoint `design.md:391-405`; canonical disclosure | MATCHES | The disclosure matches the canonical NO_COST_CHARGED text; no cost directive or prohibited deployability claim is present. |
| Frozen EXP-100 re-analysis/readiness path (`design.md:3-6`; family detail `cf-liqswp-001.md:30-62`) | No EXP-103 `analysis_code/`, source manifest, run ID, or validation artifact | MISSING | The design still names a new Nautilus `BacktestNode` vehicle. It does not pin the existing EXP-100 AMENDMENT-13 TRAIN emission, its validation artifact/hash, or the aggregate TPO contract. The family record confirms EXP-100 validity and notes that the underlying 1m path is not retained; aggregate sufficiency must be specified. |

### Golden-trace diff

No implementation or smoke emission exists, so no code/emission diff can be performed.

| Trace event | Expected from current design | Implemented/frozen evidence | Verdict |
|---|---|---|---|
| Tight profile | `VA_width=10`, `gap_span=2`, `gap_span_va=0.20`, `tight_gap=true` | No EXP-103 emission or source-column mapping | MATCHES arithmetic only |
| Non-tight profile | Same VA; selected span `101–109`, `gap_span=8`, therefore `tight_gap=false` | No EXP-103 emission or source-column mapping | MATCHES arithmetic only |
| TPO/VA/gap selection, reset, and boundary handling | Counts, fixed bin grid, exact selected mask, new-maximum reset, and strict boundary should be hand-derived | No input bars/counts/mask and no implementation | MISSING |

The design-only arithmetic is consistent. The trace is not sufficient for fresh QA of the frozen emission, and no implementation exists from which to derive an expectation.

### Governance & boundary

- **Fresh context:** PASS — recorded as `mode: subagent`; this review did not produce the implementation.
- **Family/registry:** PASS — `CF-LIQSWP-001` is `REGISTERED`; EXP-103 is registered as HYP-003; the current family/registry retain cTrader-only scope and 0 counted TEST reads.
- **Checkpoint/source-of-truth:** PASS at scope level — current checkpoint and family agree on 1W levels, AMENDMENT-13 observation-bar raid lifetime, 1H/4H confirmation, 264 cells, and the 50% tightness rule.
- **EXP-100 prerequisite:** NOT READY — the family record says EXP-100 is operator-upheld with 264/264 validity cells and complete profile coverage, but EXP-103 does not identify the exact frozen emission, validation artifact, or fields it will consume.
- **Holdout/TEST:** PASS as a declared boundary — current checkpoint/family say TRAIN only with no TEST or holdout reads; no such data was loaded or inspected in this review. Runtime enforcement is not verifiable without an EXP-103 path.
- **No Python price backtest:** PASS/N/A — no EXP-103 runner or strategy exists; no run was launched.
- **No local accounting:** NOT VERIFIABLE — there is no EXP-103 `code/` directory to check; no accounting primitive was added by this review.
- **Zero cost:** PASS at design level — canonical disclosure present; no `COST-DIRECTIVE`; no live cost call exists to inspect.
- **No research powering:** PASS — no MDE, detection floor, power curve, `UNPOWERED`, or machine value verdict appears; `INTEGRITY_Z=2.8` is used only for validity.
- **Derangement:** DESIGN DECLARED / RUNTIME UNVERIFIED — the design says zero fixed points, but no implementation regenerates or rejects fixed-point draws.
- **Battery/multi-cell/null rules:** REVISE — the 264-cell design does not carry the §13 time-stability, exit-matched-null, or derived-threshold clauses; its sample-size notes cover only the fourth clause.
- **One BacktestNode per process:** N/A for the requested frozen re-analysis; no process or runner exists. The current `Vehicle: BacktestNode` line must be reconciled with the no-new-run path.
- **XENA/SPDR/PSR:** N/A — no XENA route, SPDR conversion, or mean trade/leg bps read is declared.
- **Operator gate:** PASS — no machine value verdict is assigned; execution/final decisions remain operator gates.

### Issues

1. **HIGH — missing frozen-source contract.** `FAILING_ARTIFACT: python/experiments/EXP-103/design.md:3-6,41-71`; `REQUIRED_SKILL: quant-designer`. Pin the exact EXP-100 AMENDMENT-13 TRAIN emission/run identity, manifest or validation artifact, and aggregate profile columns; state explicitly that EXP-103 is analysis-only and launches no new `BacktestNode`, TEST, or holdout read.
2. **HIGH — outcome population is not reconciled to AMENDMENT-6.** `FAILING_ARTIFACT: python/experiments/EXP-103/design.md:20-39,73-105`; `REQUIRED_SKILL: quant-designer`. Define the primary-attributed confirmed-sweep population for later-swing contrasts, and retain non-primary/profile-only, failed, censored, and undefined rows with explicit reason codes rather than silently treating all defined profiles as outcome-bearing.
3. **HIGH — golden trace is not hand-reproducible.** `FAILING_ARTIFACT: python/experiments/EXP-103/design.md:108-117`; `REQUIRED_SKILL: quant-designer`. Add timestamped profile input bars, frozen ATR/bin width, bin counts, POC/VA expansion, selected-bin mask, 30% mass calculation, strict 50% boundary case, and the label/outcome separation. Do not derive it from the emission.
4. **MEDIUM — multi-cell governance declarations are incomplete.** `FAILING_ARTIFACT: python/experiments/EXP-103/design.md:93-106`; `REQUIRED_SKILL: quant-designer`. Add the §13 battery/eligibility/null rules for the 264-cell design and explicitly state per-stratum operator-only band handling, with no row hiding or auto-verdict.
5. **MEDIUM — control disjointness is not specified or executable.** `FAILING_ARTIFACT: python/experiments/EXP-103/design.md:73-91`; `REQUIRED_SKILL: quant-designer`, then `experiment-developer` if a runtime path is later approved. State how deranged outcome blocks are disjoint in alignment from raw outcomes and how zero fixed points are enforced and disclosed.

## QA run 3 — 2026-08-14T17:09:53Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: shared fresh-context readiness review of the current full EXP-103 design against prior
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
| Read-only 264-cell AMENDMENT-14 source, gate-first, and left join (§ Frozen source/JOIN) | `design.md:12-40`; `EXP-100/results/estimand_validation.json`; `strategy.py:235-265` | MATCHES | Source/gates are fixed; `(raid_id, profile_generation)` cardinality and left-retention rules prevent silent row loss. |
| Online TPO construction and exact outer-span convention (§ Frozen profile) | `design.md:68-88`; `tpo.py:150-202,278-310`; checkpoint §8 | MATCHES WITH REPRESENTATION NOTE | Frozen code emits inclusive outer-bin span `(high_index-low_index+1)*bin_width`. This equals `gap_high_edge-gap_low_edge`; the design's `+bin_width` index-price form is exact. |
| Population, non-tight comparator, profiles/statuses (§ Population) | `design.md:90-109`; checkpoint AMENDMENT-6; EXP-100 report `:38-85` | MATCHES | Primary-completed + DEFINED is fixed; non-primary/failed/censored/undefined/missing profiles remain reported. |
| Binding ATR_UNDEFINED exclusion (§ Frozen source; § Population) | `design.md:22-25,107-110`; checkpoint `status.md:9-21`; EXP-100 report `:58-85` | MATCHES | Affected values are excluded without reconstruction; rows/reasons remain visible. |
| Tight-minus-non-tight estimator and uncertainty (§ Population) | `design.md:107-120` | MATCHES (design-level) | Joint level-cluster circular bootstrap, sign, seeds, quantiles, sensitivity, empty arms, and unpaired proportions are pinned. No EXP-103 implementation exists. |
| Required TPO integrity checks (§ Required integrity) | `design.md:122-128`; `amendment_summary.json.failure_sums`; `tpo.py:150-202` | MATCHES | Join, conservation, fixed bins, POC/VA/gap mass, strict tightness, reset, undefined reasons, and replay are required hard reads. |
| Gap-label derangement (§ Control) | `design.md:132-152`; requirements §§3-4; L-28 | MATCHES for mapping | Labels stay fixed, outcome blocks derange with zero fixed points, and same-label donors are correctly allowed. |
| Future-destroy hard decision and fixture (§ Tripwire) | `design.md:154-163`; governance N6b; requirements §4 | MISSING / DEVIATES | Only a synthetic +0.50 ATR fixture has an inequality. The live tight-gap contrast has no hard survival rule; duration/strong-move plants, SE-of-mean-destroy computation, and collapse fraction are undefined. |
| Golden trace (§ Golden trace) | `design.md:197-216`; `tpo.py:214-310` | MATCHES | Both count fixtures reproduce POC, VA path/mass, selected mask, inclusive span, 0.40/0.60 ratios, and strict 0.50 boundary. |
| Amendment ledger/final null and canonical zero cost (§ Governance; § Zero cost) | `design.md:219-264,269-279`; checkpoint amendments 2-14; shared config canonical block | MATCHES | Complete 2L/3T/8N ledger, no machine selection, and verbatim disclosure. |

### Golden-trace diff

| Event | Expected from design | Frozen TPO mechanics | Verdict |
|---|---|---|---|
| T1 | Counts total 140; VA bins 100-104 total 114; gap bins 101-102 span 2; ratio .40; tight | Lowest POC, upper-first VA tie, density/index ordering, and inclusive span produce exactly this | MATCHES |
| T2 | Counts total 85; VA bins 101-105 total 75; gap outer bins 102-104 span 3; ratio .60; non-tight | Lower-only expansion from POC 105 and lowest-density selection produce exactly this | MATCHES |
| T3 | Ratio exactly .50 is non-tight; later outcomes cannot rewrite profile label | Source uses strict `<0.50` and finalizes the profile at confirmation | MATCHES |
| Plant/control | Every authorized outcome channel collapses and a surviving live result is invalid | Only the ATR fixture is numerically specified | MISSING |

### Governance & boundary

- Fresh-context subagent: PASS. Prior source/join, AMENDMENT-6 population, golden trace,
  multi-cell ledger, and disjointness findings are resolved.
- Registry/fence/read accounting: PASS. HYP-003 is registered with 0 candidate slots and 0
  counted TEST reads; no TEST/holdout access occurred.
- Read-only/no implementation: PASS. EXP-100 was not run or changed; EXP-103 `analysis_code/`
  is empty and no Python backtest or local accounting path exists.
- One-node, cost, powering, PSR: PASS/N/A. No new node; exact zero-cost disclosure; no live
  cost function, research power machinery, or trade/leg mean.
- Battery/null rules: PASS/N/A as declared; no selection battery, exit choice, phase-shift
  threshold, capped read, or count-based hiding.

### Issues

1. **REVISE — the hard future-destroy contract is incomplete.** `design.md:154-163` validates
   only a synthetic `swing_atr` plant. Add the same-estimator hard rule for an observed
   tight-minus-non-tight result that survives destruction, exact computation order for the
   mean-destroy SE and disclosed control/raw fraction, and numeric duration/strong-move plants
   if those channels remain in the control's authority. `FAILING_ARTIFACT: design.md`;
   `REQUIRED_SKILL: quant-designer`.

## QA run 4 — 2026-08-14T00:00:00Z — mode: subagent — HEAD unavailable

Verdict: REVISE

### Design-fidelity trace

| Design clause (§ref) | Code / artifact evidence | Verdict | Notes |
|---|---|---|---|
| Frozen source, gate-first, TRAIN fence, and left join (§1) | `python/experiments/EXP-103/design.md:7-40`; `python/experiments/EXP-103/results/estimand_validation.json` | MATCHES design-level | Gate reports `blocking_pass=true`, 264 cells, pinned manifest, and zero cost. EXP-103 runtime enforcement is absent. |
| Mechanism and estimand (§2) | `design.md:48-55` | MATCHES design-level | No EXP-103 implementation exists to verify behavior. |
| Object identity and non-overlap (§2) | `design.md:58-65` | MATCHES design-level | Correctly identifies the joined raid/profile and post-confirmation outcome window. |
| Frozen TPO profile contract (§2) | `design.md:67-86`; shared `python/src/xen/exp100/tpo.py:179-202,241-310` | MATCHES shared apparatus | Shared code emits the required profile fields and strict tightness rule. EXP-103 does not yet verify them independently. |
| Outcome population and comparator (§3) | `design.md:90-120`; EXP-100 report population/exclusion statements | MATCHES design-level | Primary-completed defined rows and non-primary/profile-only retention are stated. No EXP-103 analysis path applies the mask. |
| Estimator/bootstrap/report contract (§4) | `design.md:123-171` | MISSING runtime implementation | No `analysis_code/` module or result artifact implements the five-seed, 10,000-resample clustered analysis. |
| Profile integrity checks (§5) | `design.md:173-176` | MISSING runtime implementation | Required join, conservation, mask, replay, and exclusion checks are declared but not executable in EXP-103. |
| Future-destroy control (§6) | `design.md:178-214`; shared `python/src/xen/exp100/control.py:163-230` | DEVIATES / unverified | Design requires per-seed `default_rng(d).permutation(n)` derangements with rejection. Shared EXP-100 control uses deterministic cycle mapping and is not this HYP-003 control. |
| Tripwire and live survival rule (§6) | `design.md:216-299` | MATCHES design-level; runtime missing | Current design now includes live survival inequalities and plants for ATR, duration, and strong-move. No implementation verifies them. |
| Sample-size, hard/informative split, PSR N/A (§7) | `design.md:263-301` | MATCHES design-level | No trade/leg-bps series is declared; no PSR is required. |
| Golden trace (§8) | `design.md:303-318`; shared `tpo.py:202,241-310` | MATCHES arithmetic | T1/T2/T3 values are hand-reproducible. No EXP-103 smoke emission exists for an actual diff. |
| Amendment ledger and final selection accounting (§9) | `design.md:321-365` | MATCHES | 2 looser / 3 tighter / 8 neutral is declared; no machine selection is specified. |
| Zero-cost disclosure (§10) | `design.md:368-379`; pipeline canonical disclosure | MATCHES | Canonical `NO_COST_CHARGED` disclosure is present and no cost directive is requested. |

### Golden-trace diff

| Event | Expected from design | Implemented evidence | Verdict |
|---|---|---|---|
| T1 tight profile | Counts `[29,12,23,23,27,26]`; VA count 114; gap span 2; ratio 0.40; tight | Shared TPO logic supports strict tightness and inclusive span; no EXP-103 smoke output | MATCHES arithmetic / runtime unverified |
| T2 non-tight profile | Counts `[10,18,13,7,7,30]`; VA count 75; gap span 3; ratio 0.60; non-tight | Shared TPO logic supports lower-neighbour expansion and density selection; no EXP-103 smoke output | MATCHES arithmetic / runtime unverified |
| T3 strict boundary | `gap_span_va=0.50` produces `tight_gap=false`; label cannot be rewritten by outcomes | `tpo.py:202` uses strict `<`; no EXP-103 execution path | MATCHES shared logic / runtime unverified |
| Future-destroy plants | ATR +0.50, duration +3,600,000,000,000 ns, strong-move +0.25; all seeds satisfy validity inequalities | No EXP-103 implementation or fixture output | MISSING |

### Governance & boundary

- **Fresh context:** PASS. This review did not produce EXP-103 implementation.
- **Registry:** PASS at declaration level. Family is registered; EXP-103 is HYP-003 with 0 counted TEST reads.
- **Estimand gate:** PASS in the supplied artifact: `blocking_pass=true`, `n_cells=264`, pinned manifest, and no-cost checks pass.
- **Source seal:** NOT VERIFIABLE. EXP-103 has no analysis module to verify each cell’s `config_hash`, `event_log_sha256`, emission version, and one-node seal.
- **Holdout/TEST:** Declared TRAIN-only and no holdout was accessed during this review. Runtime enforcement is NOT VERIFIABLE.
- **No Python strategy backtest:** PASS/N/A. No EXP-103 runner exists.
- **No local accounting:** NOT VERIFIABLE. `analysis_code/` is empty; `check_no_local_accounting("python/experiments/EXP-103/code")` was not run.
- **Zero cost:** PASS at design/gate level; live analysis path does not yet exist.
- **No research powering:** PASS. No prohibited MDE, detection-floor, power-curve, or machine value labels were found.
- **Derangement:** Design PASS; runtime NOT VERIFIABLE. The shared EXP-100 cycle destroy is not the exact HYP-003 RNG/rejection contract.
- **Battery/null rules:** Design declares F02/F04/F06 not applicable and F07 satisfied. Runtime reporting of all thin/empty rows is NOT VERIFIABLE.
- **One BacktestNode:** N/A for the declared re-analysis; no new process exists.
- **PSR/XENA/SPDR:** N/A.
- **Operator gate:** PASS. No automatic value or family verdict is specified.

### Issues

1. **HIGH — EXP-103 implementation is absent.**
   **Design:** §1, `design.md:31`; §4, `design.md:123-171`.
   **Evidence:** `python/experiments/EXP-103/analysis_code/` is empty; no EXP-103 `code/`, analysis output, or smoke emission exists.
   **Why it matters:** Clause-to-code fidelity, holdout enforcement, deterministic analysis, row retention, and estimator correctness cannot be verified before execution.
   **Required owner/change:** `experiment-developer` must add the independent analysis module under `analysis_code/`, with tests/fixture output and result artifacts. It must not create a new engine run or mutate EXP-100.

2. **HIGH — Required HYP-003 future-destroy implementation is not present.**
   **Design:** §6, `design.md:178-299`.
   **Evidence:** No EXP-103 implementation. Shared `python/src/xen/exp100/control.py:163-230` implements a deterministic cycle mapping, not the required per-seed `default_rng(d)` permutation with fixed-point rejection.
   **Why it matters:** Reusing the shared apparatus would silently change the registered null control and invalidate the hard leak-validity attestation.
   **Required owner/change:** `experiment-developer` must implement the exact grouped outcome-block derangement, zero-fixed-point assertion, 2,000-destroy disclosure, outer-bootstrap SE calculation, and all three pre-read fixture channels.

3. **HIGH — Golden-trace execution diff cannot be completed.**
   **Design:** §8, `design.md:303-318`.
   **Evidence:** No EXP-103 smoke emission or analysis result exists.
   **Why it matters:** The arithmetic fixtures match the shared TPO logic, but there is no independent EXP-103 output proving the implementation preserves the frozen profile labels and strict boundary.
   **Required owner/change:** `experiment-developer` must provide a deterministic smoke/fixture result showing T1–T3 expected fields before any live source read.

4. **MEDIUM — Runtime boundary and accounting checks are unverified.**
   **Design:** §1 and §7, `design.md:31,291-301`.
   **Evidence:** No EXP-103 code exists; `check_no_local_accounting` and a source-path holdout audit were not run.
   **Why it matters:** The design’s no-source-mutation, TRAIN-only, no-TEST, and no-local-accounting claims remain assertions rather than verified properties.
   **Required owner/change:** Add the analysis path, then run `check_no_local_accounting` and the required holdout/source-seal checks before execution approval.

### Residual risks

- The supplied EXP-100 gate is valid, but EXP-103-specific source sealing and field reconciliation remain untested.
- The shared EXP-100 destroy implementation must not be treated as the registered HYP-003 control without an exact-contract review.
- No live outcome estimates or control results exist; no value interpretation is possible.

## QA run 5 — 2026-08-14T23:22:40Z — mode: subagent — HEAD 12e0b63ecc1c5a16bcca220795071f5be0bf5575

Verdict: REVISE

Scope: single exhaustive fresh-context review of the EXP-103 analysis implementation. Expected
behaviour was derived from the current design before code inspection. This review inspected the
append-only QA history, checkpoint-019 source documents through AMENDMENT-14, registry/family
records, the retained EXP-100 gate and schemas, shared TPO and estimand-boundary code, the
EXP-103 analysis module, fixture artifact, focused tests, and current git state. It did not run
live EXP-103 analysis, execute an engine, or access TEST/HOLDOUT data.

Reviewed dirty state:

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

| Design clause (§ref) | Code / artifact evidence | Verdict | Notes |
|---|---|---|---|
| Frozen EXP-100 source, gate-first, 264 cells, TRAIN fence, no engine (§1) | `analysis.py:928-996,999-1060`; copied gate is byte-identical to EXP-100 gate | DEVIATES | Gate/file/fence checks run before parquet reads and pass for 264 cells, but `config_hash` is only shape-checked and is never compared with the gate's pinned per-cell hash. Parquet inputs have no immutable digest check. |
| One-to-one raid/profile left join and census retention (§1) | `analysis.py:310-354,1045-1059` | MATCHES join; MISSING report | Duplicate/missing/extra keys block and every raid is retained in memory. The live entry point emits only total row count, so the required per-cell join census is never persisted. |
| Binding ATR-undefined exclusion (§1/§3) | `analysis.py:61-69,124-178,656-664,723-743` | MATCHES primary channels | `swing_atr` and `strong_move` exclude affected rows; duration remains readable. Exclusion counts exist in helper output but are not emitted by the live entry point. |
| Frozen TPO profile rules and hard reconciliation (§2/§5) | shared `python/src/xen/exp100/tpo.py:142-207,241-311`; `analysis.py:357-430` | DEVIATES | EXP-103 checks scalar ratios and truthiness only. It does not parse masks, verify mask/span, POC, VA expansion/tie order, 30% selected mass, bin assignment, bracket conservation, reset-on-new-maximum, or deterministic replay. It labels replay attested without performing it. |
| Primary population and exact fixed comparator (§3) | `analysis.py:656-743` | PARTIAL | The primary-completed/defined filter and tight-minus-non-tight arm are present. The second emitted arm is `False - False`, not the required all-defined descriptive baseline. |
| Primary/secondary estimands and duration alias (§3) | `analysis.py:124-178,688-693,1052-1054` | DEVIATES | Alias is asserted. Runtime composition includes only `swing_atr`, duration, and `strong_move`; it omits finite `swing_price`/`swing_bps`, all-defined summaries, displayed duration hours, and the required secondary disclosures. |
| Joint whole-level circular bootstrap, 5 seeds, 10,000 draws, L=2/5/10 (§4) | `analysis.py:83-121,181-236,667-720` | DEVIATES | The helper implements the core joint cluster draw, but orchestration requests only `L=5`. Sparse resamples with an empty arm silently make the entire quantile/SE output NaN. L=2/L=10 and their sensitivity outputs are absent. |
| Neutral observed/ideal/interpretation handoff, every row, no machine value label (§4/§7) | `analysis.py:667-743,1063-1083` | MISSING | No live result writer or report-layer artifact exists; `--live` stops after printing `rows`. Required estimates, intervals, counts, reasons, strata, exclusions, controls, and symmetric evidence cannot be handed to the analyst. |
| Exact grouped cross-gap derangement (§6) | `analysis.py:239-307,869-917` | DEVIATES | Zero-fixed-point complete-block movement is implemented. Groups with `n<2` remain unchanged inside the contrast; their VOID is only counted and does not invalidate the affected channel/stratum. Non-finite destroyed draws are silently removed and the required destroyed 95% interval/VOID detail is not emitted. |
| Same-estimator outer-bootstrap tripwire (§6) | `analysis.py:746-866` | DEVIATES | The live rule has the declared SE families, but can return `ATTESTED_OR_NOT_APPLICABLE` despite `VOID_NO_DERANGEMENT`. The executable path expands to 5 x 10,000 x 2,000 deep-copy derangements per arm/stratum and is invoked for a redundant second arm, making the registered full run operationally infeasible. |
| Pre-read future-destroy plant and fixture topology (§6) | `analysis.py:433-653`; `results/fixture_integrity.json` | DEVIATES | All three planted channels currently pass, but the fixture outer step resamples the two arms independently with iid row choices (`analysis.py:489-517`), not jointly from the registered circular level-cluster sequence. The fixture therefore does not prove the live estimator/control contract. |
| Sample-size context, no powering, PSR N/A (§7) | `design.md:273-310`; `analysis.py` denylist scan | MATCHES at code level | No MDE, power floor, row-count veto, or trade/leg-bps read exists. Thin rows are not deliberately hidden, but missing live orchestration prevents the required reporting. |
| Golden trace T1/T2/T3 (§8) | `tests/test_exp10x_analysis_contract.py:140-162`; `analysis.py:357-430` | MISSING | The lone T1-like scalar test checks only a changed ratio. No T2/T3 output exists, and malformed/missing masks, POC, VA path, and selected mass can pass the integrity function. |
| Amendment accounting (§9) | `design.md:333-371`; code denylist scan | MATCHES | No machine qualification/selection or family disposition was added. |
| Canonical zero-cost disclosure (§10/N9) | `analysis.py:612-646`; `results/fixture_integrity.json:4-10` | DEVIATES | No cost function is called, but the results artifact omits `prohibited_claims` and `lifting` and changes the canonical text, so it does not carry the required verbatim disclosure. |

### Golden-trace diff

| Event | Expected from design | Implemented evidence | Verdict |
|---|---|---|---|
| T1 tight profile | POC 100; VA 100-104/count 114; selected 101-102; span 2; ratio .40; tight | Shared EXP-100 TPO code supports the arithmetic. EXP-103 test supplies final scalars only and never proves POC/VA/mask construction. | MISSING EXP-103 trace |
| T2 non-tight profile | POC 105; VA 101-105/count 75; selected 103/104/102; span 3; ratio .60; non-tight | No EXP-103 fixture/test/output. | MISSING |
| T3 strict boundary | ratio .50 is non-tight; outcomes cannot rewrite the label; non-primary stays profile-only | Scalar strict `<` is checked in `profile_integrity_report`; no boundary fixture or label-immutability trace is emitted. | PARTIAL |
| Future-destroy plants | +0.50 ATR, +3.6e12 ns, +0.25; joint level-cluster outer bootstrap; every seed raw-bite/destroyed-non-bite | Artifact reports all three plants passing with 2,000 derangements and zero fixed points, but uses a different arm-wise iid outer resampler. | DEVIATES |

### Governance & boundary

- **Fresh context:** PASS — this subagent did not produce the implementation.
- **Registry/read accounting:** PASS — `CF-LIQSWP-001/HYP-003` is registered; 0 counted TEST reads; no TEST/HOLDOUT access occurred.
- **Source gate/fence:** PARTIAL — the static 264-cell gate-first/hash check passed, but the pinned config hash is not compared and input parquet identity is not sealed by EXP-103.
- **No Python backtest / one node:** PASS — analysis-only module; no `BacktestNode` or engine execution.
- **No local accounting:** PASS — `check_no_local_accounting(...)` returned `ok=true`; no experiment code is imported.
- **Zero cost:** PARTIAL — no live cost path, but fixture/results disclosure is not canonical.
- **Future destroy:** REVISE — derangement core exists; singleton/null-class VOID propagation and exact fixture estimator do not.
- **Neutrality/powering/PSR:** PASS for prohibited value machinery; REVISE for incomplete reporting. PSR is correctly N/A because there is no trade/leg-bps estimand.
- **Prior findings:** implementation now exists and basic derangement/boundary fixtures pass. Prior missing-runtime, full golden-trace, and exact control-contract findings are not completely resolved.

### Issues

1. **CRITICAL — the live command does not execute or save the registered analysis.**
   **Design:** §3-§7, `design.md:93-310`.
   **Evidence:** `analysis.py:667-743,1063-1083` reads all live rows and prints only their count. Its only composed bootstrap uses `L=5`; it omits L=2/L=10 sensitivity, all-defined baseline, `swing_price`/`swing_bps`, duration hours, result layers, and result persistence. It also emits a meaningless `False - False` arm (`analysis.py:736-743`).
   **Impact:** there is no executable path that can produce the predeclared evidence package; running `--live` can appear successful while answering none of HYP-003.
   **Required change:** implement one bounded live orchestrator that writes every predeclared per-stratum observed result/reason/exclusion for the tight-minus-non-tight comparison and all-defined disclosure, all three block lengths/five seeds, with no value verdict.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`.
   **REQUIRED_SKILL:** `data-analyst`.

2. **CRITICAL — an undestroyable singleton nullness group can remain in the control and still receive a non-VOID status.**
   **Design:** §6, `design.md:178-255`.
   **Evidence:** `analysis.py:275-304` leaves every `n<2` group unchanged; `analysis.py:897-917` includes those unchanged outcomes in destroyed contrasts and does not propagate VOID into integrity status. Focused reproduction: one singleton nullness group remained unchanged, `void_no_derangement=3`, yet duration returned `ATTESTED_OR_NOT_APPLICABLE`.
   **Impact:** the hard future-destroy validity check can certify a contrast partly containing future outcomes it never destroyed.
   **Required change:** make any affected stratum/channel explicitly VOID before interpretation (or predeclare and implement a valid exclusion/reconciliation rule); preserve every row and full VOID disclosure. Add regression tests for mixed derangeable/singleton nullness groups and non-finite draws.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`, `python/tests/test_exp10x_analysis_contract.py`.
   **REQUIRED_SKILL:** `data-analyst`.

3. **HIGH — declared profile integrity and golden-trace checks are not implemented.**
   **Design:** §2, §5, §8, `design.md:73-91,166-173,312-331`.
   **Evidence:** `analysis.py:357-430` accepts masks by truthiness and declares replay attested. A focused malformed row with nonsense masks, no POC/VAL/VAH/bracket count, and no selected-mass proof returned `blocking_pass=true`. Tests cover neither T2 nor T3 (`test_exp10x_analysis_contract.py:140-162`).
   **Impact:** mask/span drift, POC/VA tie errors, gap-mass errors, reset drift, or replay drift can pass this hard source attestation.
   **Required change:** parse and reconcile emitted masks and all declared scalars/identities; consume a pinned EXP-100 replay/integrity receipt where raw reconstruction is intentionally forbidden; add exact T1-T3 expected fixtures and fail-closed tests for each hard check.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`, `python/tests/test_exp10x_analysis_contract.py`, fixture result.
   **REQUIRED_SKILL:** `data-analyst`.

4. **HIGH — bootstrap behavior is incomplete for sensitivity and invalid for thin joint resamples.**
   **Design:** §4, `design.md:123-141`.
   **Evidence:** `analysis.py:688-693` requests only L=5. `analysis.py:208-235` feeds NaN empty-arm replicates directly to `np.quantile`/`np.std`; a two-cluster valid source (one cluster per arm) produced a finite contrast but NaN bounds/SE without a reason. The fixture outer bootstrap independently resamples arms (`analysis.py:489-517`) instead of using the registered joint circular cluster sequence.
   **Impact:** predeclared L=2/L=10 evidence is absent, thin strata can lose all uncertainty output silently, and the pre-read fixture does not validate the live estimator.
   **Required change:** implement/report all L values, define and emit fail-closed empty-resample accounting without hiding the stratum, and use the exact joint whole-level circular estimator in the fixture and live tripwire.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`, `python/tests/test_exp10x_analysis_contract.py`, `python/experiments/EXP-103/results/fixture_integrity.json`.
   **REQUIRED_SKILL:** `data-analyst`.

5. **HIGH — the registered control path is computationally non-runnable as written.**
   **Design:** §6-§7, `design.md:227-255,291-296`.
   **Evidence:** `outer_bootstrap_integrity` performs 5 x 10,000 x 2,000 = 100,000,000 Python `future_destroy` calls per arm/stratum (`analysis.py:822-860`), each deep-copying/traversing the rows. `analyze_strata` invokes it for both `False-False` and `True-False` arms (`analysis.py:686-700`). With up to 528 side-specific strata this is over 100 billion deep-copy derangement calls, before ordinary bootstrap outputs, and has no progress path.
   **Impact:** the one-shot analysis cannot complete in a practical run; partial/manual shortcuts would silently deviate from the registered estimator.
   **Required change:** algebraically/vectorially reuse each deterministic mapping across channels and bootstrap populations while preserving exact membership, ordering, null classes, seeds, and denominators; remove the redundant arm; add parity tests against a small explicit reference and progress reporting.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`.
   **REQUIRED_SKILL:** `data-analyst`.

6. **HIGH — the frozen-source seal is not actually pinned to the accepted gate.**
   **Design:** §1, `design.md:12-32`.
   **Evidence:** `analysis.py:974-995` checks only that `run_metadata.config_hash` looks like a 64-character string; it never compares it to `cell.catalog_attestation.config_hash`, even though the copied accepted gate carries that value. Only `event_log.jsonl` is hashed; `raids.parquet`, `tpo_profiles.parquet`, and `bar_marks.parquet` have no immutable identity check.
   **Impact:** a changed config or changed verdict-bearing parquet can be read as the retained operator-approved source while the gate still appears passing.
   **Required change:** compare every available gate pin byte-for-byte and add/consume a frozen manifest containing digests for every verdict-bearing input; fail before parquet reads on any mismatch.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py` plus the frozen-source manifest/receipt.
   **REQUIRED_SKILL:** `data-analyst` (coordinate any missing immutable receipt with the EXP-100 artifact owner; do not mutate or rerun EXP-100).

7. **HIGH — the fixture results artifact violates the mandatory zero-cost disclosure contract.**
   **Design:** §10, `design.md:374-388`; neutrality N9.
   **Evidence:** `analysis.py:612-646` and `results/fixture_integrity.json:4-10` omit `prohibited_claims` and `lifting` and alter the canonical implication wording. The artifact also has no explicit statement that no cost function entered the fixture calculation beyond the shortened object.
   **Impact:** the required boundary can disappear or weaken on downstream results despite code currently charging no costs.
   **Required change:** emit the canonical disclosure verbatim and completely on every results/report artifact; add an exact-string regression test.
   **FAILING_ARTIFACT:** `python/experiments/EXP-103/analysis_code/analysis.py`, `python/experiments/EXP-103/results/fixture_integrity.json`, `python/tests/test_exp10x_analysis_contract.py`.
   **REQUIRED_SKILL:** `data-analyst`.

### Focused commands run

```text
PYTHONPATH=src .venv/bin/pytest -q tests/test_exp10x_analysis_contract.py
# 16 passed in 0.32s
PYTHONPATH=src .venv/bin/ruff check experiments/EXP-103/analysis_code/analysis.py tests/test_exp10x_analysis_contract.py
# All checks passed
check_no_local_accounting('experiments/EXP-103/analysis_code')
# {'ok': True, 'banned_defs_found': []}
gate_first('../data/nautilus_runs/EXP-100/full', EXP-103 copied gate)
# verified_cells=264; gate blocking_pass=true
fixture-only deterministic smoke
# completed; all three planted channels reported pass
focused malformed-profile, singleton-VOID, thin-bootstrap, and orchestration probes
# reproduced issues 1-4 above without live-source analysis
```
