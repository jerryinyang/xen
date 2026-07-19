---
name: chapter-rollover
description: >
  Roll the Xen research programme from one chapter of experiments to the next via three
  phases — Extract (distil hard-won knowledge into a curated knowledge base + project
  memory), Archive (move the chapter's experiments and docs into a git-tracked archive and
  reset to clean skeletons), and Renew (apply a prompted-in change-set of improvements to
  the pipeline, skills, referee framework, or conventions). Use when starting a new
  research chapter, closing the current chapter, decluttering python/experiments and
  docs/experiments-docs, capturing programme knowledge before a reset, or applying a
  system-wide pipeline/framework update at a chapter boundary. Triggers: roll the chapter,
  close the chapter, start a new chapter, chapter boundary, chapter transition, extract
  archive renew, new experiment chapter, reset the research slate.
---

# Chapter Rollover

Roll the research programme from one experiment chapter to the next. The mechanism is fixed
(Extract → Archive → Renew); the content of Renew is supplied per invocation, which is what
makes this skill reusable at every chapter boundary.

## Inputs

1. **Chapter id** — the chapter being *closed*: `chapter-NN-<slug>` (NN zero-padded). If
   unknown, derive NN from the highest existing `archive/chapter-*` (or `01` if none) and
   ask the operator for the slug/theme.
2. **Renew change-set** — the specific improvements to apply this rollover, prompted in at
   invocation. Renew has **no default content**: if none is supplied, ask for it before
   starting Renew (Extract and Archive can proceed without it).

## Order of operations

Run the phases **in order** — each depends on the previous:

1. **Extract first**, while the chapter's artifacts are still in place and rich.
2. **Archive second**, to declutter once knowledge is captured.
3. **Renew third**, so edits land on a clean pipeline.

Do not reorder. Announce the phase before starting it.

## Phase 1 — Extract

Distil the closing chapter's knowledge into a curated, read-first knowledge base plus a
parallel atomic project memory, so the next chapter never re-runs dead directions or
re-learns amendment-lessons.

Follow `references/extract-checklist.md`. Key points:
- Build/refresh the seven `docs/knowledge-base/` files; use `bmad-distillator` for lossless
  compression of heavy source docs.
- `lessons-and-amendments.md` is the critical file — every lesson needs an explicit
  **mechanism (why)**, not just the numeric symptom.
- Maintain `docs/knowledge-base/memory/` atomic facts + `MEMORY.md` index.
- The signal-registry stays **live** and is referenced, never copied.

## Phase 2 — Archive

Move the chapter's experiments and docs into an in-repo, git-tracked archive and reset the
active tree to clean skeletons — losing nothing, contaminating nothing.

Follow `references/archive-procedure.md`. Key points:
- `git mv` (preserve history); never delete-and-recreate.
- Prune `python/src/xen/` to the neutral reusable core; **confirm the keep/prune list with
  the operator before moving**. Contaminated modules (leak/bias sources named by a lesson)
  are snapshotted but excluded from the live core.
- Reset `python/experiments/` and `docs/experiments-docs/` to skeletons; keep
  `docs/knowledge-base/` and the live `docs/signal-registry/`.
- Tag `chapter-NN-close`.

## Phase 3 — Renew

Apply the prompted-in change-set to the research system, then propagate each change into the
knowledge base so it becomes part of the read-first canon.

Follow `references/renew-protocol.md`. Key points:
- One focused edit per change-set item; keep artifacts lean.
- Every change must be reflected in `docs/knowledge-base/` **with its mechanism**, and must
  name the check/file that now **enforces** it (not advisory-only).
- Guardrails regardless of content: the holdout fence is non-negotiable; preserve
  causal-by-construction leak resistance; never reset the multiplicity/test-read ledger.

## Finish

1. Write the rollover report: `archive/chapter-NN-<slug>/ROLLOVER.md` (see
   `references/renew-protocol.md` for the structure).
2. Verify deterministically:
   ```bash
   python3 .claude/skills/chapter-rollover/scripts/verify_rollover.py --root . --chapter NN
   ```
   Resolve any `FAIL` before declaring the rollover complete.

## Operator-facing communication (binding)

Phase announcements, confirmation asks, and finish summaries to the human are **concise and
de-jargonified**. Full rules: `research-pipeline/_pipeline-config.md` § *Operator-facing
communication* (also project `AGENTS.md` §5). Plain meaning first; irreversible steps as
clear yes/no with consequence; no process jargon walls.

## Hard constraints

- Never read, load, or inspect the global holdout during any phase.
- Confirm irreversible moves (the `src` prune) with the operator first.
- Preserve git history on every move; tag the chapter close.
- Renew without a supplied change-set is incomplete — ask, do not invent one.

## References

| Resource | Read when |
|----------|-----------|
| `references/extract-checklist.md` | Phase 1 — KB + project memory taxonomy and acceptance |
| `references/archive-procedure.md` | Phase 2 — git-mv steps, src keep/prune, skeleton reset |
| `references/renew-protocol.md` | Phase 3 — consuming the change-set, report, acceptance |
| `scripts/verify_rollover.py` | Finish — deterministic post-rollover state check |
