# Programme reference set

This directory is the live, chapter-agnostic source of truth for the Xen research programme. The documents here state the rules, data contracts, architecture, and operating procedures that apply to current work.

They are deliberately self-contained. A historical experiment, plan, or temporary note may explain how a rule was discovered, but it is not required to interpret or apply the rule recorded here.

## Governing documents

| Document | Governs |
|---|---|
| [governance.md](governance.md) | Programme-wide boundaries, validity, evidence, and operator authority |
| [neutrality-standard.md](neutrality-standard.md) | Neutrality, zero-cost disclosure, PSR, and powering-strip rules |
| [architecture.md](architecture.md) | Event-driven execution, data flow, fences, and emissions |
| [dataset-reference.md](dataset-reference.md) | Materialized datasets, schemas, paths, and split facts |
| [spdr-lane.md](spdr-lane.md) | Lightweight screening-lane procedure |
| [xena-lane.md](xena-lane.md) | Portfolio-construction-lane procedure |
| [xena-run-design-template.md](xena-run-design-template.md) | Pre-registration template for a portfolio-construction run |

## Authority rules

- If a prior experiment changed a current rule, the operative rule is written here rather than delegated to that experiment.
- Current data claims must describe materialized files and pinned facts. A run-created output path is identified as such; an empty clean slate is not described as containing results.
- Gross, cost-free research results are not cost-complete, tradable, deployable, or investment performance.
- Validity failures invalidate an observation; they are not converted into negative evidence.
- Counts, effect estimates, uncertainty, and diagnostics are evidence. The operator assigns the final disposition.
- Historical material is context only and cannot silently override this set.
