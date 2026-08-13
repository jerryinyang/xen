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
