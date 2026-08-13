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
