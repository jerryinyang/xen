---
name: research-pipeline
description: Orchestrate the Xen research experiment lifecycle from idea or EXP-ID through mechanism-first design, fresh-context QA, engine execution, estimand validation, data analysis, and operator verdict. Use when starting a new experiment, resuming a partial experiment, designing experiment scope, running the research pipeline end to end, continuing an EXP or VAL item, or enforcing the Xen experiment process.
---

# Research Pipeline (INFR-001 Orchestrator)

Coordinate the experiment workflow; route work to specialists; enforce the split:
**machines gate integrity; the operator judges value.** Hard blocks exist only for integrity
(**future-destroy** leak survival, holdout, causality/provenance, estimand reconciliation).
Every quality or materiality read is informative — presented as evidence, decided by the operator.

**INFR-016 (2026-07-18):** value/quality/significance reads are **report layers**
(`observed / ideal / interpretation` per candidate — `xen.xena.report_layer`), never gates.
Nothing is machine-dropped between layers; the operator authorises which candidates advance.
The only hard checks are **data-validity attestations** (holdout, causal ≤t-1, estimand
reconciliation, non-STUB fence, no-local-accounting, future-destroy leak survival).

## Start

1. Read `_pipeline-config.md` (this skill directory).
2. Read `docs/knowledge-base/INDEX.md`, `lessons-and-amendments.md`, `pitfalls-ledger.md` —
   mandatory before design.
3. Read `docs/references/dataset-reference.md`, `architecture.md`.
4. Read `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`, the newest active
   checkpoint `design.md`, and `docs/signal-registry/` preconditions.
5. Determine entry point: **XENA run (the DEFAULT for a new idea — see XENA lane below)**,
   new EXP, resume EXP, VAL re-analysis, SPDR speed-run screen (see SPDR carve-out below),
   or scope-only design. EXP/SPDR require explicit operator invocation for new ideas.

## Stages

```
1 Design ............ quant-designer                    → design.md
2 QA pre-exec ....... qa-compliance (FRESH context)     → qa-review.md (append-only)
    [OPERATOR GATE — execution approval]
3 Execute ........... Nautilus BacktestNode run         → data/nautilus_runs/<run_id>/
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

All strategy logic runs in the **NautilusTrader** event-driven engine (`BacktestNode`).
A vectorised Python backtest of a price strategy is REJECT-class. **VAL carve-out:**
re-analysis of already-emitted, still-valid data skips stages 1-3 and enters at the estimand
gate → `data-analyst` (archived cTrader emissions under chapter-03 archive only).

**XENA lane (DEFAULT route, INFR-006).** An incoming idea becomes candidates in a XENA
universe: Nautilus emission per candidate (shim → adjudication; `SlPrice` on legs) →
blocking candidate gate (`xen.xena.ingest.gate_universe`) → LAHC search on the TRAIN
search band → plateau + disjoint-fold certification (evidence package, operator reviews) →
operator-approved counted final gate on TEST (`run_final_gate`; ledger cap 2/universe;
`new_data_attestation` operator-only). **VOID on new stack (INFR-010 R4):** chapter-03
frozen registry pins are invalid for Bybit/crypto until a fresh CAL INFR produces a new
hash-pinned registry. Spec: `docs/references/xena-lane.md` v2.

**SPDR carve-out (speed-run screens).** The `SPDR-###` lane is a TRAIN-only availability
screen that runs vectorised in Python to gate a `WORTH_EXPLORING` disposition **before** a
full experiment — it is NOT a tradability claim and never touches TEST/holdout, spends a
read, or registers a family. It is permitted only inside the hard integrity boundary
(TRAIN-only fence + causal `t-1` lag, code-asserted; matched-control + seed battery;
per-stratum). A `WORTH_EXPLORING` graduates the idea into the standard Nautilus
price-primary pipeline. Full spec + stages + artifacts: `docs/references/spdr-lane.md`.

## Per-experiment artifacts

```
python/experiments/<ID>/
├── design.md          # quant-designer (mandatory declaration blocks)
├── qa-review.md       # qa-compliance, append-only across reruns
├── code/              # developer: Nautilus strategy/runner refs (no Python analysis)
├── analysis_code/     # data-analyst's own scripts
├── results/           # incl. estimand_validation.json (gate artifact)
├── plots/
├── analysis.md        # data-analyst: evidence for+against + recommended verdict — UNCAPPED
└── report.md          # documenter: record incl. the OPERATOR's final verdict
```

## Operator gates (the only stops)

The only machine stops are **holdout-safety + data validity** (INFR-016). Everything else is
**operator-authorised layer progression**: report layers describe every candidate; the operator
decides which advance.

1. **Execution approval** (mandatory, after QA APPROVE) — operator may rerun QA first.
2. **Final experiment verdict** (after `analysis.md`).
3. Spending a counted TEST read — additionally requires a passing
   `estimand_validation.json` for the emission being read (pre-read gate).
4. Anything holdout-adjacent; any deployability claim.
5. **Layer progression** — after each report layer, the operator authorises which candidates
   advance to the next layer. No value read auto-drops a candidate.

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

## Operator-facing communication (binding — all skills, all stages)

**Every message to the human operator** (question, status, progress report, gate prompt,
summary, handoff, recommendation) must be **concise and de-jargonified**. Full rules and
templates: `_pipeline-config.md` § *Operator-facing communication*.

Short form (never skip):
- Lead with plain meaning; technical labels only in parentheses if needed once.
- Status ≤8 short lines; summary ≤15 unless more was requested.
- Questions: one plain sentence; options with one-line consequences; recommendation marked.
- On-disk artifacts may stay precise; chat that reports them must translate.
- 20-second test: if a smart non-specialist owner would not get it, rewrite.

If a question cannot be stated plainly, investigate first — do not dump process jargon.

## Hard constraints

- Knowledge base before design; never re-run a `pitfalls-ledger.md` dead end.
- Never load/inspect the final-30% global holdout (both sanctioned shots spent).
- Nautilus execution for all edge generation; real prices; `ts_event`/`SourceCloseTime`
  alignment (never bar indices); decisions at bar open on confirmed bars (`≤ t-1`);
  open-to-open returns; catalog fence + emission attestation (STUB fails v2 gate).
- Estimands come from `xen.adjudication`; no accounting primitives in experiment dirs
  (`check_no_local_accounting`).
- No verdict, control read, or TEST read on an emission without a passing estimand gate.
- Per-stratum reads; pooled figures are disclosure-only.
- Register candidates before screening; counted TEST reads recorded (cap 2 lifetime/stratum).
- No scope expansion after QA APPROVE — new questions are new experiments.
- No auto-verdicts: quality thresholds do not gate; the operator decides. Value/quality/
  significance reads are **report layers** (`observed/ideal/interpretation`), never gates
  (INFR-016). Retired auto-verdicts: `at_or_above_p95` sign-battery boolean, `n_legs_floor`
  veto, `one_subset` top-1 hiding, derangement `hard_fail_leak` collapse<0.5, final-gate
  `passed`. Only **future-destroy** leak survival + holdout + causal + estimand stay hard.

## References

| Resource | Read when |
| --- | --- |
| `_pipeline-config.md` (this skill) | Always |
| `docs/knowledge-base/` | Always, before design |
| `references/governance-constraints.md` | QA stage; TEST-read gate |
| `references/scope-design.md`, `experiment-templates.md` | Stage 1 |
| `python/experiments/INFR-010/code/emission_contract_v1.md` | Execution + estimand gate |
| `xen.nautilus.*` | Nautilus runner + shim |
| `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md` | Start, completion |
| `docs/signal-registry/` | Stage 1 precondition; Stage 6 evidence rows |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | Start, phase alignment |
| `docs/references/spdr-lane.md` | Any `SPDR-###` speed-run screen |
| `docs/references/xena-lane.md` | Any XENA run (the default route for new ideas) |
