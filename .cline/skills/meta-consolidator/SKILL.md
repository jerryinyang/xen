---
name: meta-consolidator
description: >-
  Deprecated placeholder. This skill is intentionally disabled for Xen because
  no Xen-specific multi-reviewer consolidation workflow has been designed yet.
  Do not use unless a new Xen meta-consolidation workflow is explicitly created.
---

# Meta-Consolidator Deprecated

## Operator-facing output (binding)

Every message to the human (question, status, summary, gate, handoff): **concise, plain
language, de-jargonified**. Lead with meaning; technical labels in parentheses only if
needed once. See project `AGENTS.md` §5 (and, for research skills,
`research-pipeline/_pipeline-config.md` § *Operator-facing communication*). On-disk
technical artifacts may keep precise terms; chat to the operator must translate.

This skill is intentionally inactive for Xen.

The previous consolidation workflow depended on project-specific experiment
batches and strategy synthesis rules that do not apply to the current Xen
research setup. Do not invoke this skill for Xen research planning, experiment
execution, or documentation.

If Xen later needs multi-reviewer consolidation, create a new Xen-specific
workflow with explicit inputs, outputs, inclusion rules, and governance checks.
