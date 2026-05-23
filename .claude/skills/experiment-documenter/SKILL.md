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
   - `docs/experiments-docs/INDEX.md`
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

Update `docs/experiments-docs/INDEX.md` with the detailed five-field schema:

- Hypothesis Tests
- Scope
- Results / Observations
- Hypothesis-Specific Conclusion
- Hypothesis-Agnostic Observations

Only include hypothesis-agnostic observations when the evidence is direct and unambiguous.

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
| `docs/experiments-docs/INDEX.md` | Before and after detailed index updates |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | When findings affect phase direction |
