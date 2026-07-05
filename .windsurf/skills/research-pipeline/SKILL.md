---
name: research-pipeline
description: Orchestrate the Xen research experiment lifecycle from idea or EXP-ID through mechanism-first design, fresh-context QA, engine execution, estimand validation, data analysis, and operator verdict. Use when starting a new experiment, resuming a partial experiment, designing experiment scope, running the research pipeline end to end, continuing an EXP or VAL item, or enforcing the Xen experiment process.
---

# Research Pipeline (INFR-001 Orchestrator)

Coordinate the experiment workflow; route work to specialists; enforce the split:
**machines gate integrity; the operator judges value.** Hard blocks exist only for integrity
(leak tripwire, holdout, causality/provenance, estimand reconciliation). Every quality or
materiality read is informative — presented as evidence, decided by the operator.

## Start

1. Read `_pipeline-config.md` (this skill directory).
2. Read `docs/knowledge-base/INDEX.md`, `lessons-and-amendments.md`, `pitfalls-ledger.md` —
   mandatory before design.
3. Read `docs/references/dataset-reference.md`, `architecture.md`.
4. Read `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`, the newest active
   checkpoint `design.md`, and `docs/signal-registry/` preconditions.
5. Determine entry point: new EXP, resume EXP, VAL re-analysis, or scope-only design.

## Stages

```
1 Design ............ quant-designer                    → design.md
2 QA pre-exec ....... qa-compliance (FRESH context)     → qa-review.md (append-only)
    [OPERATOR GATE — execution approval]
3 Execute ........... cTrader CLI run                   → data/strategy_runs/<ID>/
4 Estimand gate ..... xen.estimand_validation (script)  → results/estimand_validation.json
5 Data analysis ..... data-analyst                      → analysis.md
    [OPERATOR — final experiment verdict]
6 Document .......... experiment-documenter             → report.md + indexes
```

| Stage | Skill | Notes |
| --- | --- | --- |
| Design | `quant-designer` | mechanism-first; mandatory declaration blocks (its `design-requirements.md`) |
| QA | `qa-compliance` | **spawn as a subagent** (fresh context by construction) or the operator runs it in a new session; rerunnable; APPROVE required before the execution gate |
| Execute | orchestrator | **operator-gated**: credentials/cost + this is the mandatory approval point; operator may demand more QA runs first, run it manually, or approve an orchestrator run |
| Estimand gate | script | `python -m xen.estimand_validation <family_root> --expect <instruments> --out python/experiments/<ID>/results/estimand_validation.json` — `blocking_pass` required before ANY analysis, verdict, or TEST read |
| Analysis | `data-analyst` | own code, canonical `xen` estimands, evidence for+against, recommended verdict only |
| Verdict | **operator** | decides on the analyst's evidence; may order follow-up probes (analyst reruns Phase 2) |
| Document | `experiment-documenter` | records the operator's verdict + evidence; experiment-level registry rows only |

## Every experiment is price-primary

All strategy logic runs in the cTrader engine (C# `ISignalModel`, `tools/ctrader-cli/`).
A Python backtest of a price strategy is REJECT-class. **VAL carve-out:** re-analysis of
already-emitted, still-valid data skips stages 1-3 and enters at the estimand gate →
`data-analyst`. If the prior emission is invalidated by an identified defect, a rerun (full
pipeline) is required first.

## Per-experiment artifacts

```
python/experiments/<ID>/
├── design.md          # quant-designer (mandatory declaration blocks)
├── qa-review.md       # qa-compliance, append-only across reruns
├── code/              # developer: C# refs + confs notes (no Python analysis)
├── analysis_code/     # data-analyst's own scripts
├── results/           # incl. estimand_validation.json (gate artifact)
├── plots/
├── analysis.md        # data-analyst: evidence for+against + recommended verdict — UNCAPPED
└── report.md          # documenter: record incl. the OPERATOR's final verdict
```

## Operator gates (the only stops)

1. **Execution approval** (mandatory, after QA APPROVE) — operator may rerun QA first.
2. **Final experiment verdict** (after `analysis.md`).
3. Spending a counted TEST read — additionally requires a passing
   `estimand_validation.json` for the emission being read (pre-read gate).
4. Anything holdout-adjacent; any deployability claim.

## Experiment vs family (binding separation)

- An experiment produces **evidence and an experiment-level verdict**. It never opens,
  closes, retires, or promotes a candidate family.
- Family status changes happen ONLY at a **checkpoint retrospective**, operator-signed.
- Registry updates during an experiment: append evidence/disposition rows only — never a
  status transition.
- **Checkpoints group multiple experiments** (a phase container). Do not open a checkpoint
  for a single experiment.

## Resume detection

Resume at the first missing artifact: no `design.md`→Design; no `qa-review.md` APPROVE→QA;
no emission→execution gate; no passing `estimand_validation.json`→estimand gate; no
`analysis.md`→Analysis; no operator verdict→present evidence; no `report.md`→Document.
Announce the resume point.

## Elicitation standard (all skills, all stages)

Questions to the operator: one plain sentence per question; concrete options with one-line
consequences; recommendation marked; no compound questions; no jargon walls. If a question
cannot be stated plainly, the asker does not understand it yet — investigate first.

## Hard constraints

- Knowledge base before design; never re-run a `pitfalls-ledger.md` dead end.
- Never load/inspect the final-30% global holdout (both sanctioned shots spent).
- Engine execution for all edge generation; real prices; `CloseTime`/`SourceCloseTime`
  alignment (never bar indices); decisions at bar open on confirmed bars (`≤ t-1`);
  open-to-open returns.
- Estimands come from `xen.adjudication`; no accounting primitives in experiment dirs
  (`check_no_local_accounting`).
- No verdict, control read, or TEST read on an emission without a passing estimand gate.
- Per-stratum reads; pooled figures are disclosure-only.
- Register candidates before screening; counted TEST reads recorded (cap 2 lifetime/stratum).
- No scope expansion after QA APPROVE — new questions are new experiments.
- No auto-verdicts: quality thresholds do not gate; the operator decides.

## References

| Resource | Read when |
| --- | --- |
| `_pipeline-config.md` (this skill) | Always |
| `docs/knowledge-base/` | Always, before design |
| `references/governance-constraints.md` | QA stage; TEST-read gate |
| `references/scope-design.md`, `experiment-templates.md` | Stage 1 |
| `tools/ctrader-cli/README.md` | Execution |
| `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md` | Start, completion |
| `docs/signal-registry/` | Stage 1 precondition; Stage 6 evidence rows |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | Start, phase alignment |
