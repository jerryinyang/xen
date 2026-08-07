# Renew Protocol — Apply the Prompted-In Change-Set

Renew is the **variable** phase. Unlike Extract and Archive (fixed procedures), Renew
applies a change-set that is **prompted in at invocation** — the specific improvements the
operator wants made to the research system this rollover. It is the reason the skill is
reusable: the mechanism is constant, the content changes each chapter.

Run Renew **after** Archive, so edits land on a clean pipeline rather than one buried in the
prior chapter's artifacts.

## Inputs

A renew change-set is a list of targeted modifications. Each item names:
- **Target** — which part of the system changes (a pipeline/specialist skill, the
  referee/eval framework, code conventions, data architecture, governance constraints).
- **Change** — what to add/alter/remove.
- **Rationale** — usually a lesson from `docs/knowledge-base/lessons-and-amendments.md`.

If the operator did not supply a change-set, stop and ask for one — Renew has no default
content.

## Procedure

For each change-set item:

1. **Locate** the target file(s). Pipeline/specialist skills live under `.claude/skills/`;
   framework/convention/architecture docs under `docs/`.
2. **Apply** the change as a focused edit. Keep artifacts lean — regulate verbosity; do not
   add bulk the next chapter must read past.
3. **Propagate to canon**: update `docs/knowledge-base/` (and project memory) so the new
   rule is part of the read-first canon, with its mechanism. A renew change that is not
   reflected in the KB will be silently lost at the next rollover.
4. **State enforcement**: name the check/file that now enforces the change, so it is not
   advisory-only.

## Cross-cutting guardrails (apply regardless of change-set content)

- **Holdout fence is non-negotiable** under any new autonomy or execution privilege.
- **Leak resistance**: any change touching how edges are generated or evaluated must
  preserve causal-by-construction guarantees and the leak-tripwire discipline.
- **Registry continuity**: the multiplicity registry and test-read ledger keep their
  mechanism across the rollover; regulate format for efficiency, never reset the ledger.

## Rollover report

After all three phases, write a concise `archive/chapter-NN-<slug>/ROLLOVER.md`:
- chapter id + theme;
- Extract: KB files written/updated, lessons carried forward;
- Archive: what moved, src keep/prune decisions, close tag;
- Renew: each change-set item, the files touched, and where it is now enforced;
- verification results (from `scripts/verify_rollover.py`).

## Renew acceptance

- Every change-set item is applied and reflected in `docs/knowledge-base/`.
- Each change names its enforcement point.
- `ROLLOVER.md` exists and summarizes all three phases.
