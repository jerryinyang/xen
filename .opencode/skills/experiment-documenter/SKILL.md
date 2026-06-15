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
   - `scope.md`
   - `analysis-plan.md`
   - `code/`
   - `results/`
   - `audit.md`
   - `results.md`
   - `governance/`
   - `plots/`
4. Read current indexes:
   - `python/experiments/INDEX.md`
   - `docs/experiments-docs/INDEX.md` (master navigation: live status + `Family Indexes` table)
   - the relevant family detail index under `docs/experiments-docs/families/<family>/INDEX.md`
   - the signal registry under `docs/signal-registry/` (candidate-family file, `multiplicity-registry.md`, `test-read-ledger.md`) when the result is registry-relevant
5. Read the bundled report templates in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-documenter/references/report-templates.md`.

## Report Workflow

Create `python/experiments/<ID>/report.md`.

Include:

- research question or hypothesis;
- scope boundaries and exclusions;
- method summary;
- key quantitative results with sample sizes and effect sizes;
- audit caveats;
- conclusion using the approved result category;
- links to code, results, plots, audit, and governance artifacts;
- follow-up recommendations as separate future experiments.

Use key plots only. Do not embed every generated plot unless each one materially supports the conclusion.

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

Record a signal-registry disposition for every experiment. If the result is registry-relevant, update `docs/signal-registry/` in the same change: advance the candidate-family status in `candidate-families/<family>.md` (e.g. `SCREENED`, `RETIRED`), record the item's outcome in `multiplicity-registry.md` (refuted/blocked/inconclusive items are retained — never deleted or renamed), and enter any counted TEST read or disclosure in `test-read-ledger.md`. If it is not (e.g. a VAL/INFR integrity run with no candidate screen), state `registry: not applicable — <reason>` in `report.md`. These follow the phase checkpoint's G0/D0 conventions — do not invent a parallel scheme.

## Writing Rules

- Prefer plain English and concrete values.
- Treat negative, refuted, and inconclusive results as useful findings.
- Separate factual observations from interpretation.
- Link artifacts with relative paths.
- Keep the report concise enough to support future review.
- Do not introduce new claims that are absent from `results.md`, `audit.md`, or raw outputs.

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
