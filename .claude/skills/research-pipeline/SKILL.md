---
name: research-pipeline
description: Orchestrate the Xen research experiment lifecycle from idea or EXP-ID through merged design, implementation, execution, audit, and documentation, with inline governance. Use when starting a new experiment, resuming a partial experiment, designing experiment scope, running the research pipeline end to end, continuing an EXP or VAL item, or enforcing the Xen experiment process.
---

# Research Pipeline (Lean Orchestrator)

Coordinate the experiment workflow and enforce the project gates. Route work to specialists;
do not replace them. This pipeline is the **token-efficient** successor to the Chapter-01
8-stage flow: **four artifacts, inline governance, autonomous execution.**

## Start

1. Read the bundled pipeline config (`_pipeline-config.md` in this skill directory).
2. Read the curated knowledge base **first**: `docs/knowledge-base/INDEX.md` and, at minimum,
   `lessons-and-amendments.md` (the leak that shipped a false positive) and
   `pitfalls-ledger.md` (dead ends — do not re-run). This is mandatory, not optional.
3. Read `docs/references/dataset-reference.md` and `docs/references/architecture.md`.
4. Read `python/experiments/INDEX.md` (next EXP-ID) and `docs/experiments-docs/INDEX.md`
   (live status). Open the newest active checkpoint `design.md` for phase objectives.
5. Check the live signal-registry preconditions (`docs/signal-registry/`).
6. Determine entry point: new EXP, resume EXP, VAL rerun, or scope-only design.

## Routing

| Need | Skill | Artifact (one each) |
| --- | --- | --- |
| Merged scope + analysis plan | `experiment-quant-analyst` | `design.md` |
| Implementation | `experiment-developer` | `code/` |
| Code + result validation | `experiment-auditor` | `audit.md` (uncapped) |
| Interpretation + final report + indexes | `experiment-documenter` | `report.md` |

The orchestrator runs governance **inline** (no separate governance artifacts) and **executes**
the experiment itself (no manual handoff) — except at the operator-gated critical decisions below.

## Price-primary vs analysis-only (binding routing)

Classify every experiment before design:

- **Price-primary** — generates signals/entries/positions/edges from price. It **must** run in
  the cTrader engine (StrategyHost mode) via `tools/ctrader-cli/run-experiment.sh`, emit
  `data/strategy_runs/<ID>/` under the `AnalysisEndUtc` fence, and be analysed in Python only on
  the emitted runs. A vectorized Python backtest of a price strategy is a **REJECT** (this is the
  L-01 structural fix; see `docs/knowledge-base/lessons-and-amendments.md`).
- **Analysis-only** — Python operating solely on emitted strategy-run / timebar parquet extracts.
  Never regenerates signals or edges.

See `tools/ctrader-cli/README.md` for the harness recipe.

## Per-experiment artifacts

```
python/experiments/<ID>/
├── design.md     # scope + analysis plan (quant-analyst) — inline pre-exec gate recorded here
├── code/         # implementation (developer); price-primary → C# model + <ID>.conf
├── results/      # emitted/computed outputs
├── plots/
├── audit.md      # validation + verdict forensics + causal-provenance (auditor) — UNCAPPED
└── report.md     # interpretation + results + final report (documenter) — inline post-exec gate
```

`design.md` and `report.md` are size-capped (see config); `audit.md` is **not** (forensic /
adversarial / causal-provenance work needs room). No `governance/` directory.

## Resume detection

Resume at the first missing/incomplete artifact: no `design.md`→Design; no `code/`→Implement;
no `results/`→Execute; no `audit.md`→Audit; `audit.md` with an unresolved Critical→fix+re-execute;
no `report.md`→Document. Announce the resume point.

## Stage 1 — Design (quant-analyst → `design.md`)

Invoke `experiment-quant-analyst` to produce the merged **scope + analysis plan**: one
falsifiable question; data views/instruments/features/params/time-range/exclusions; the
mandatory final-30% holdout exclusion; measurable success/failure/inconclusive criteria;
complexity budget; metric denominators + zero-baseline behavior; the **price-primary vs
analysis-only** classification; methods with per-stratum (non-pooled) binding endpoints,
shape-aware reads, and predeclared interpretation criteria; and the **leak tripwire(s)** the
experiment will ship (a future-destroying control that must collapse the edge).

**Inline pre-exec gate.** The orchestrator reviews `design.md` against
`references/governance-constraints.md` and the checkpoint `design.md`, and records a one-block
verdict **inside `design.md`** (`GATE: APPROVE` / `REVISE <issues>` / `REJECT <reason>`). Route
REVISE to the analyst (≤2 cycles). Registry precondition: the candidate family / variant /
parameter branch must be registered in `docs/signal-registry/` and any TEST-stratum read must
state the stratum's counted-read tally (cap 2). A scope missing these gets REVISE.

## Stage 2 — Implement (developer → `code/`)

Invoke `experiment-developer`. For **price-primary**: a C# `ISignalModel` + the
`tools/ctrader-cli/experiments/<ID>.conf`; Python only ingests/validates. For **analysis-only**:
Python on emitted extracts. Require the leak tripwire(s) to be implemented and a code-standards
+ provenance self-check (`experiment-developer/references/code-conventions.md`). The orchestrator
folds the implementation review into the pre-exec gate (no separate artifact).

## Stage 3 — Execute (orchestrator, autonomous)

The orchestrator runs the experiment — **no manual handoff**:
- analysis-only / local cached replays → run directly;
- **price-primary credentialed/cost-bearing cTrader-CLI runs are a CRITICAL DECISION** →
  confirm with the operator before running (credentials/cost), then run.
Never load the final-30% holdout. Outputs to `results/` (and `data/strategy_runs/<ID>/`).

## Stage 4 — Audit (auditor → `audit.md`)

Invoke `experiment-auditor`. The audit must carry, autonomously: **verdict forensics**
(per-stratum re-derivation + masking check + mechanism + gate-shape check) **and the new
causal-provenance & leak pass** (trace every verdict-bearing column's input timestamps; confirm
the leak tripwire collapsed the edge; verify shared-module provenance contracts). Numeric
reproduction alone is **not** an audit — it cannot see acausal provenance (L-01).

**Materiality gate (blocking).** Any finding that could move sample membership, a denominator, a
metric, temporal/causal validity, the verdict, or the binding stratum is verdict-material →
fix (`experiment-developer`) and **re-execute** (return to Stage 3) before Stage 5. A surviving
edge under a future-destroying control, or a missing provenance trace on a deployability claim,
is a REJECT-class finding.

## Stage 5 — Document (documenter → `report.md`)

Invoke `experiment-documenter` to produce the consolidated **interpretation + results + final
report** in `report.md` (interpretation is routed to the quant-analyst and written into this one
file — no separate `results.md`), plus the index and registry updates. Keep it dense (tables/
bullets, key plots only); if `report.md` or `design.md` reads wordy, run `/caveman-compress
<abs-path>` (format-only pass; preserves code/tables/numbers; delete the `.original.md` backup
before commit). See the verbosity-discipline section in `_pipeline-config.md`.

**Inline post-exec gate.** The orchestrator reviews `audit.md`, `report.md`, and index/registry
updates against `references/governance-constraints.md` and records a one-block verdict **inside
`report.md`** (`GATE: APPROVE` / `REVISE` / `REJECT`). Confirm: verdict forensics + causal-
provenance pass present; per-stratum masking check done; every verdict-material finding was
fixed-and-rerun; a signal-registry disposition recorded (and, if registry-relevant, candidate
status advanced, multiplicity outcome recorded, any counted TEST read entered). Missing any of
these → REVISE.

## Critical decisions (operator-gated — the only stops)

The orchestrator otherwise runs autonomously, but **must** pause for the operator on:
spending a counted TEST read; opening/retiring a candidate family; any deployability claim;
credentialed/cost-bearing cTrader-CLI runs; and anything holdout-adjacent.

## Completion

Report: artifacts written (`design.md`, `code/`, `audit.md`, `report.md`), the one-line key
finding, the registry disposition, and the path to `report.md`.

## Hard constraints

- Read the knowledge base before designing; never re-run a `pitfalls-ledger.md` dead end.
- Never load/inspect the final-30% global holdout. Both sanctioned holdout shots are spent.
- Price-primary edges run in the cTrader engine; a vectorized Python backtest of a price
  strategy is REJECT. Outcomes/returns use emitted **real** prices, never synthetic chart prices.
- Use `CloseTime` / `SourceCloseTime` for temporal alignment, never bar indices. No data after an
  event's timestamp may inform that event.
- Evaluate every decision at the action bar's **open** on confirmed bars only (`≤ t-1`); never read
  the forming bar's own OHLC. Returns are **open-to-open** — `OnClose` is not executable live, so an
  open-to-close return is a labelled non-tradable diagnostic only.
- Per-stratum binding verdicts; a pooled/aggregated figure is disclosure-only until cross-stratum
  homogeneity is shown.
- Register a candidate before screening it; never spend a TEST read without recording it (cap 2
  lifetime/stratum). Refuted/blocked/inconclusive items stay in the registry — never deleted.
- Do not expand scope after the pre-exec gate. New questions → new experiment.
- Do not accept performance optimizations that compromise correctness, causality, denominators,
  metric definitions, or streaming validity.

## References

| Resource | Read when |
| --- | --- |
| `_pipeline-config.md` (this skill) | Always |
| `docs/knowledge-base/` (INDEX, lessons, pitfalls) | Always, before design |
| `docs/references/dataset-reference.md`, `architecture.md` | Always |
| `references/governance-constraints.md` | Pre-exec and post-exec gates |
| `references/scope-design.md`, `experiment-templates.md` | Stage 1 |
| `tools/ctrader-cli/README.md` | Price-primary design/execution |
| `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md` | Start, completion |
| `docs/signal-registry/` | Stage 1 precondition; gates; Stage 5 updates |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | Start, phase alignment |
