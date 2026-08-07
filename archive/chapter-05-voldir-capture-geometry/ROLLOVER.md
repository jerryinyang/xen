# Chapter 05 Rollover — VolDir Capture Geometry

**Closed:** 2026-08-07

**Archive:** `chapter-05-voldir-capture-geometry`

**Close tag:** `chapter-05-close`

**Scope closed:** checkpoints 016 / 017 / 018; family `CF-VOLDIR-001` (RETIRED — characterised, not tradable); experiments `INFR-021`, `SPDR-011`…`SPDR-018B`, `SPDR-021`…`SPDR-024`.

## Extract

Chapter 05 was distilled into the live read-first canon before experiments moved.

- Updated: `docs/knowledge-base/{INDEX,families-explored,lessons-and-amendments,methodology-canon,pitfalls-ledger}.md` (and related KB surfaces).
- Lessons carried forward include **L-56** ⭐ (detection floor must share the effect's scale; design-time estimand ceiling) and companion L-57…L-61 where booked in the extract.
- Pitfall **P-28** (power constant as significance bar / wrong-scale floor).
- Atomic memory added/updated: `chapter05-dispositions.md`, `detection-floor-must-share-scale.md`, `joint-sits-at-breakeven-cost-not-rate.md`, `wl-is-the-mirror-of-p.md`, `per-notional-blind-to-size.md`, `gate-implies-label-and-live-controls.md`, plus `MEMORY.md` index lines.
- Checkpoint-018 retrospective closed as **CAPTURE GEOMETRY CHARACTERISED / NO EXTRACTABLE EDGE AT THE MEASURED JOINT**; `CF-VOLDIR-001` retired characterised-not-tradable (operator-signed).
- Signal registry, multiplicity history, test-read ledger, and holdout obligations remained live (registry not archived).

## Archive

All moves used `git mv`; the archive is a historical snapshot, not an active research input.

### Experiments and documentation

- 14 experiment directories: `INFR-021`, `SPDR-011`…`SPDR-018B`, `SPDR-021`…`SPDR-024`, plus the prior chapter INDEX.
- Prior `docs/experiments-docs/` tree for the chapter (checkpoints, families, reflections, INDEX).

### Source prune (operator-confirmed)

**Archived thesis-specific stack:**

- `python/src/xen/adaptive_management/` → `archive/.../python-src/adaptive_management/`
- Adaptive-management + SPDR-024 + SPDR-011 + chapter-05 preflight tests → `tests-deprecated/`

**Kept live (neutral core):**

- Root: `__init__.py`, `adjudication.py`, `estimand_validation.py`, `evaluation.py`, `bar_aggregator.py`
- Packages: `nautilus/`, `sigbar/`, `xena/`, plus retained `signals/`, `indicators/`, `orderflow/` (not flagged contaminated; only the adaptive-management device stack was chapter-thesis-specific)

### Data purge (permanent; operator-confirmed)

- Deleted all of `data/nautilus_runs/` (full run emission set for the chapter).
- SPDR-024 raw untracked emissions under experiment `results/runs/` (~7.1 GB) purged as regenerable; durable analysis parquets retained inside the archived experiment tree.
- **Kept:** `data/catalog`, `data/catalog_ctrader`, `data/catalog_sigbar`.

### Active slate after archive

- `python/experiments/INDEX.md` skeleton only; no live experiment dirs.
- `docs/experiments-docs/` skeleton (empty checkpoints/families/reflections + INDEX).
- Pruned core pytest: **198 passed, 4 skipped, 0 failures** (recorded during Archive phase).

## Renew

Single change-set item (operator-supplied at rollover start): **codify the SPDR-024 MDE-floor fix (AMENDMENT-7 R1–R5) as programme-wide apparatus.**

| Change | Files | Enforcement |
|---|---|---|
| Analysis-time floor/ladder rules R1–R5 | `.claude/skills/data-analyst/SKILL.md` Phase 2; `references/interrogation-protocol.md` (Q14–16 + failure table) | Data-analyst must not use power constants as row pass marks; floors same-SE as CI; no floor-derived row labels; per-channel `sigma_denominator` |
| Design-time ceiling + power contract | `.claude/skills/quant-designer/references/design-requirements.md` §6 | Every design declares same-SE floor definition, channel denominators, and per-cell algebraic ceiling / capability before run |
| Canon already carried L-56 / P-28; enforcement paths updated post-archive | `docs/knowledge-base/lessons-and-amendments.md` L-56 **Enforced at**; pitfalls **P-28**; methodology-canon Chapter 05 additions; memory `detection-floor-must-share-scale.md` | Read-first KB + skill contracts; historical SPDR-024 analyser lives only under the chapter archive |

Skill mirrors: edit landed in `.claude/skills` (canonical); `scripts/sync_skills.sh` re-mirrors to other agent trees.

## Verification

```bash
python3 .claude/skills/chapter-rollover/scripts/verify_rollover.py --root . --chapter 05
```

Expected: all deterministic checks PASS, including git tag `chapter-05-close`.

Sampled history: `git log --follow` on an archived experiment path still resolves (moves via `git mv`).
