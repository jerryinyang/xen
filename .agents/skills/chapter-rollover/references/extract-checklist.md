# Extract Checklist — Knowledge Base + Project Memory

The goal of Extract is a **functional, LLM-optimized knowledge base** the next chapter
reads *first*, so dead directions are never re-run and amendment-lessons are never
re-learned. Distil the closing chapter's heavy artifacts (master INDEX, family indexes,
checkpoints, reflections, registry) into durable, scannable canon.

Use `bmad-distillator` for lossless compression of heavy source docs into KB files.
**Do not copy the signal-registry into the KB** — it stays live (programme-level
multiplicity persists across chapters) and is *referenced* from the KB.

## A1. Curated KB — `docs/knowledge-base/`

Create/refresh these files. Each is canonical and append-merged at every rollover (a new
chapter adds/updates entries; it does not wipe prior canon).

| File | Must capture |
|------|--------------|
| `INDEX.md` | Read-first navigation + a "what's FROZEN / what's OPEN" summary. Links every KB file and the live signal-registry. |
| `data-architecture.md` | The data layer + the cTrader strategy-host contract: base data, derived views, strategy_runs parquet schema, holdout fence. Distil from `docs/references/architecture.md`, `dataset-reference.md`, pipeline config. |
| `evaluation-framework.md` | The **frozen** evaluation frame: sample-size context + direct baseline comparison + PSR + zero-cost model (INFR-022) — what must **not** be re-derived. **Do NOT freeze per-domain MDE maps or detection floors as live apparatus** (INFR-022 powering strip): mention them only as historical superseded apparatus with their supersession banner. Gate stack, adopted operating point, incremental/portfolio-fitness unit history may be noted as historical record with `superseded-for-live-use` framing. |
| `families-explored.md` | Every candidate family + hypothesis + **disposition** (dead / refuted / inconclusive / open). Anchor on the live decision frame (e.g. the availability 2×2). One row per family; link its archived family index. |
| `methodology-canon.md` | Productive vs futile methods: what to do (e.g. availability-screen-first, matched-random controls, multiplicity-adjusted admission gates, per-stratum non-pooling, inverted-inference predeclaration) and what wastes effort. |
| `lessons-and-amendments.md` | **The critical file.** Every observation that forced an amendment, each with its **mechanism (the WHY)** — not just the numeric symptom. A lesson without a mechanism is incomplete. |
| `pitfalls-ledger.md` | Refuted directions / dead ends that must never be re-run, each with the evidence that closed it. |

### The lessons-and-amendments mandate

This is the file that prevents reverting to past mistakes. For each entry:

- **What happened** — the bug/confound/false result (1–2 lines).
- **Mechanism (why)** — the concrete causal reason it occurred and slipped through. This
  is mandatory; re-deriving the numbers is not an explanation.
- **The fix / new rule** — what changed in the pipeline, skills, or framework.
- **Where it's enforced now** — the file/check that catches it going forward.

Seed entries the rollover must preserve (carry forward, do not lose):
look-ahead favourable-index leak in a shared outcome module; booked-vs-real feed
divergence + binding-leg entry slippage; pooled-verdict masking; gross→net cost trap;
cross-regime null-variance in permutation design.

## A2. Parallel project memory — `docs/knowledge-base/memory/`

Append-as-you-go atomic facts (one fact per file) with frontmatter + a `MEMORY.md` index
line per file. In-repo and chapter-spanning. This is the lightweight companion to the
curated KB: KB = structured canon refreshed at boundaries; project memory = incremental
atomic facts captured during day-to-day work.

Frontmatter shape:

```markdown
---
name: <kebab-slug>
description: <one-line summary for recall>
metadata: { type: project | reference | lesson, chapter: <N> }
---
<the fact; link related entries with [[slug]]>
```

Distinct from the user-global `~/.claude/.../memory` (which keeps only cross-project
pointers). Do not duplicate the curated KB here — memory holds atomic facts, KB holds canon.

## Extract acceptance

- `docs/knowledge-base/INDEX.md` resolves and links all seven KB files + the live registry.
- Each seeded lesson in `lessons-and-amendments.md` has an explicit **mechanism** line.
- `docs/knowledge-base/memory/MEMORY.md` exists with one pointer line per memory file.
- The signal-registry (`docs/signal-registry/`) is untouched and still live.
