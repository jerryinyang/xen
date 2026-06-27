# Archive Procedure — Clean, Non-Contaminating Slate

The goal of Archive is to declutter the active working set so the next chapter starts
clean, **without losing anything**: artifacts move to an in-repo, git-tracked archive that
stays reachable for code-convention reference but is far enough from the active tree not to
contaminate the new chapter.

Run Archive **after** Extract (the KB must capture the chapter's knowledge while the
artifacts are still in place).

## Hard rules

- **Preserve git history**: move with `git mv`, never delete-and-recreate.
- **Confirm before irreversible moves**: the `src` keep/prune split (below) is reviewed
  with the operator before any move. Mitigated by the close tag, but confirm anyway.
- **Never touch the holdout**: archiving reads no data; the global holdout fence is
  untouched.
- **The signal-registry stays live** — it is *not* archived. Programme-level multiplicity
  and the test-read ledger persist across chapters.

## Steps

1. **Resolve chapter id**: `chapter-NN-<slug>` (NN zero-padded, slug from the chapter's theme).

2. **Create the archive root**: `archive/chapter-NN-<slug>/`.

3. **`git mv` into the archive**:
   - all experiment dirs: `python/experiments/EXP-*`, `VAL-*`, `INFR-*`;
   - the experiment-docs snapshot: `docs/experiments-docs/` (`INDEX.md`, `families/`,
     `checkpoints/`, `reflections/`);
   - chapter-specific tooling: per-experiment run scripts and `reports/` under
     `tools/ctrader-cli/` (keep generic scripts + credentials/env in place).

4. **Prune `python/src/xen/` to the neutral reusable core.** Classify each module:
   - **KEEP (neutral infrastructure)** — generators, resamplers, the referee/calibration
     and portfolio/fitness machinery, walk-forward, availability gates, financing,
     read-only ingestion. Reusable by any thesis.
   - **ARCHIVE (thesis-specific)** — signal/strategy modules tied to the closing chapter's
     families (the chapter's specific entry/exit/geometry/screen modules).
   - **ARCHIVE AND DO NOT CARRY FORWARD (contaminated)** — any module a lesson flagged as a
     leak/bias source. Snapshot it into the archive but exclude it from the live core so it
     cannot be re-imported. (Chapter 01: `intrabar_fill.py`, the look-ahead favourable
     index source.)

   Snapshot the full `src` into the archive first, then prune the live tree. Present the
   keep/prune list and get explicit confirmation before pruning.

5. **Reset to skeletons** (keep the directories, empty the contents):
   - `python/experiments/` — no `EXP-*` dirs; fresh `INDEX.md` (header + empty table).
   - `docs/experiments-docs/` — fresh master `INDEX.md` (live-status skeleton), empty
     `checkpoints/`, empty `families/` (new families created as the chapter opens them).
   - Leave `docs/knowledge-base/` (just populated) and `docs/signal-registry/` (live) in place.

6. **Tag the close**: `git tag chapter-NN-close` at the rollover commit.

## Archive acceptance

- `archive/chapter-NN-<slug>/` exists and is non-empty.
- `python/experiments/` has no `EXP-*` dirs and a fresh `INDEX.md`.
- `docs/experiments-docs/INDEX.md` exists; `checkpoints/` is empty.
- `docs/signal-registry/` is still present and live.
- `git log --follow` on a sampled moved file shows preserved history.
- `git tag` lists `chapter-NN-close`.
