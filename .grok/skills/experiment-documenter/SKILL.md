---
name: experiment-documenter
description: Document completed Xen experiments and maintain experiment indexes. Use when writing report.md, summarizing experiment findings, updating python/experiments/INDEX.md, updating docs/experiments-docs/INDEX.md, recording negative or inconclusive results, or responding to prompts such as document, write report, summarize, update docs, experiment report, findings, or write up results.
---

# Experiment Documenter

Turn validated experiment artifacts into durable project documentation.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md`.
3. Read the full experiment package:
   - `design.md` (mechanism-first scope + plan)
   - `qa-review.md` (fresh-context pre-exec review runs)
   - `code/` and `analysis_code/`
   - `results/` incl. `estimand_validation.json` (and `data/strategy_runs/<ID>/`)
   - `analysis.md` (data-analyst: evidence for+against + recommended verdict)
   - the **operator's final verdict** (from the conversation/decision record — the report
     records it; the documenter never substitutes its own)
   - `plots/`
4. Read current indexes:
   - `python/experiments/INDEX.md`
   - `docs/experiments-docs/INDEX.md` (master navigation: live status + `Family Indexes` table)
   - the relevant family detail index under `docs/experiments-docs/families/<family>/INDEX.md`
   - the signal registry under `docs/signal-registry/` (candidate-family file, `multiplicity-registry.md`, `test-read-ledger.md`) when the result is registry-relevant
5. Read the bundled report templates in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-documenter/references/report-templates.md`.

## Report Workflow

Assemble the **consolidated** `python/experiments/<ID>/report.md`. Keep it within the size
cap (≈400 lines); dense, not verbose.

Include:

- research question or hypothesis + mechanism statement;
- scope boundaries and exclusions;
- method summary;
- **key quantitative evidence** from `analysis.md`: effect sizes with uncertainty, sample
  sizes, per-stratum (non-pooled) results, collapse fractions, evidence for AND against;
- integrity-gate results (estimand validation, tripwire, provenance) and analysis caveats;
- **the operator's final verdict**, recorded verbatim, with the analyst's recommendation
  noted separately if they differ;
- links to `design.md`, `qa-review.md`, `analysis.md`, code, results, plots;
- follow-up recommendations as separate future experiments;
- the signal-registry disposition (evidence rows only — see below).

Use key plots only. Do not embed every generated plot unless each one materially supports the
conclusion. There is no separate `results.md` or `governance/` directory.

## Index Updates

Update `python/experiments/INDEX.md` with a concise row:

```markdown
| <ID> | <title> | <status> | <one-line finding> | <date> |
```

Add the detailed per-experiment card to the **relevant family detail index** — `docs/experiments-docs/families/<family>/INDEX.md`, not the master — using the five-field schema:

- Hypothesis Tests
- Scope
- Results / Observations
- Hypothesis-Specific Conclusion
- Hypothesis-Agnostic Observations

Only include hypothesis-agnostic observations when the evidence is direct and unambiguous. Append the new card under the family's experiment list and add its entry to that family's in-file ToC.

Choose the family by candidate family / programme era (see the master `Family Indexes` table): e.g. `cf-ha-harami-001` for Phase 014 work, `infrastructure-validation` for VAL-/INFR-series. If the experiment opens a new candidate family, create `docs/experiments-docs/families/<new-family>/INDEX.md` (header + overview + ToC, mirroring the existing family indexes) and add a row to the master `Family Indexes` table.

In the master `docs/experiments-docs/INDEX.md`, update **only** the live-status blocks — `Current Checkpoint Status`, `Current Infrastructure Tasks`, `Checkpoint Retrospectives`, and the `Family Indexes` table (EXP range / status). Do not add per-experiment cards to the master.

Record a signal-registry disposition for every experiment — **evidence rows only** (INFR-001
experiment/family separation): record the item's outcome in `multiplicity-registry.md`
(refuted/blocked/inconclusive items retained — never deleted or renamed) and enter any counted
TEST read or disclosure in `test-read-ledger.md`. **Never change a candidate-family status**
(open/RETIRED/promoted) from within an experiment — family status transitions happen only at a
checkpoint retrospective, operator-signed; append the experiment's evidence to
`candidate-families/<family>.md` without touching its status field. If not registry-relevant
(e.g. a VAL/INFR integrity run), state `registry: not applicable — <reason>` in `report.md`.

## Writing Rules

- Prefer plain English and concrete values.
- Treat negative, refuted, and inconclusive results as useful findings.
- Separate factual observations from interpretation.
- Link artifacts with relative paths.
- Keep the report concise enough to support future review.
- Do not introduce new claims that are absent from `analysis.md` or raw outputs.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled report templates | Before writing `report.md` |
| `python/experiments/INDEX.md` | Before and after index updates |
| `docs/experiments-docs/INDEX.md` (master) | Before and after live-status / `Family Indexes` updates |
| `docs/experiments-docs/families/<family>/INDEX.md` | Before and after detailed per-experiment card updates |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | When findings affect phase direction |
