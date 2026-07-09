# Checkpoint 007 — CF-VOLHARV-001 Falsification-First Screen (2026-07-04)

**Phase container** for the first CF-VOLHARV-001 experiment set. Predecessor: checkpoint-006
(CF-MR-005 disposition — RETIRED; cross-instrument MR arc closed). Family card:
`docs/signal-registry/candidate-families/cf-volharv-001.md`. Registration row:
`multiplicity-registry.md` Chapter-02 CF-VOLHARV-001 section.

## Why this family, why this shape

The MR arc's post-mortem (`.ignore/temp/new-family/analysis-1.md`, `analysis-2.md`): every
conditioned directional claim died on the cost/capture wall or attribution; the only positive
residues in two chapters are two-sided, magnitude-shaped, unconditioned objects (EXP-018 rt
anomaly; CF-VOLEXP-001 tail hint). Checkpoint-006 sanctioned the vol-harvest reframing as a
new-family route. The founding anomaly is theoretically impossible in expectation
(fixed-unit random-dir random-timing fixed-hold ⇒ E[gross]=0), so the phase opens with its
kill test, not with a harvest screen — the programme's falsification-first norm applied to
its own discovery.

## Phase objectives

1. **Adjudicate the anomaly** (EXP-019 / HYP-001): reproducible across ex-ante seeds, or a
   draw? Either answer closes the question permanently.
2. **Measure the harvest cost floor** (EXP-019 disclosure): swap-inclusive carrying cost per
   instrument × hold at 1× and 2× — the input no prior family ever had before betting.
3. **Profile the substrate** (EXP-019 disclosure): VR/oscillation amplitude at 6/12/24/48
   bars per instrument — where could a harvest structure plausibly clear the floor?
4. **Decide HYP-002** at the retrospective: scope EXP-020 (rebalanced-exposure / grid
   harvest) on instruments where (3) clears (2), or retire the family at 0 reads / 0 slots.

## Planned work

| Item | What | Gate |
|---|---|---|
| INFR (swap table) | Declared per-instrument per-night swap/financing table in `xen.evaluation`, version-pinned, snapshot-dated; 1× + 2× columns; triple-swap calendar | lands before any EXP-019 analysis read |
| EXP-019 | HYP-001 falsification battery: 16 instruments × 25 seeds × hold grid {6,12,24,48}, 4h TRAIN, RandomHoldModel, native orders, m1 fills; + NZDUSD +1-bar delay twin | design done → QA (fresh context) → operator execution gate → estimand gate → analysis → operator verdict |
| EXP-020 | HYP-002 harvest-structure screen | design-gated on this retrospective; NOT scoped in this phase |

## Constraints in force

- TRAIN only (first 49% per instrument); TEST band never emitted; holdout sealed; 0 slots,
  0 counted reads by construction.
- Integrity gates hard (schedule byte-diff, fill causality, estimand reconciliation,
  holdout); every quality read informative — operator judges (INFR-001 frame).
- Family status can change ONLY at this checkpoint's retrospective, operator-signed.
- Predeclared kill criteria: family card §Kill criteria.

## Exit condition

Retrospective written when EXP-019 has an operator verdict and the HYP-002 scope/retire
decision is made. Possible phase outcomes: (a) anomaly artifact + no viable floor-clearing
substrate → RETIRE at 0 cost; (b) anomaly artifact + substrate viable → scope EXP-020;
(c) PROCESS_ASYMMETRY → fill-forensics experiment supersedes everything (would implicate
more than this family).
