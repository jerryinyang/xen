# Chapter 01 → 02 Rollover Report

**Chapter closed:** `chapter-01-price-geometry-referee` (the chart-type → single-series
price-geometry families + the frozen referee framework era; ~98 experiments, ~25 phases).
**Date:** 2026-06-27. **Driver:** a look-ahead leak shipped a false `DEPLOYABLE_CONFIRMED`
(CF-MR-001, retracted) — see knowledge base L-01.

## Extract

Curated knowledge base written at `docs/knowledge-base/` (read-first canon):
`INDEX`, `data-architecture`, `evaluation-framework` (frozen suite + MDE floors),
`families-explored` (dispositions + the availability 2×2), `methodology-canon`,
`lessons-and-amendments` (L-01…L-11, each with mechanism), `pitfalls-ledger` (P-01…P-09 dead
ends). Parallel project memory at `docs/knowledge-base/memory/` (5 seed atomic facts + index).
The live signal-registry (`docs/signal-registry/`) was left in place and referenced, not copied.

## Archive

- `git mv` → `archive/chapter-01-price-geometry-referee/`: all experiments (EXP/VAL/INFR),
  `experiments-docs/` (master INDEX, families, checkpoints, reflections), Chapter-01 cTrader
  outputs + per-experiment run scripts, and 5 family test files.
- `python/src/xen/` pruned to a **19-module import-clean neutral core** (data-layer generators,
  frozen referee/calibration/portfolio-fitness, walk-forward, availability gate, vol-regime,
  financing, expectancy, portfolio, domain_bars, move_position, cross_sectional, ass,
  capture_barriers, ingestion, indicators). 21 thesis-specific modules archived to
  `src-archived/xen/`; `intrabar_fill.py` + `mean_reversion.py` flagged **contaminated, do not
  carry forward** (`src-archived/DO-NOT-CARRY-FORWARD.md`). `compression_primitives` archived
  (cascaded into closed-family cores; Screen-M primitive to be re-implemented cleanly).
- Skeletons reset: fresh `python/experiments/INDEX.md`, fresh
  `docs/experiments-docs/INDEX.md` + empty `checkpoints/` + `families/`. Signal-registry live.
- Neutral-core tests pass (15/15) + the new leak canary (2/2).

## Renew (change-set applied)

| Item | What changed | Enforced at |
|------|--------------|-------------|
| **C1 anti-bias** | Causal-provenance & leak audit pass (independent of numeric reproduction); mandatory leak tripwires; shared-module provenance contracts; ban the `rct[di]` pattern; booked-vs-real binding-leg slippage | `experiment-auditor/SKILL.md` + `references/audit-checklists.md`; `experiment-developer/SKILL.md` + `references/code-conventions.md`; `research-pipeline/references/governance-constraints.md` (new REJECT triggers); KB L-01/L-02; regression `python/tests/test_leak_canary.py` |
| **C2 cTrader-primary** | Price-primary experiments run in-engine (look-ahead impossible by construction); Python analysis-only; reusable harness scaffolded (`run-experiment.sh`, `experiments/EXAMPLE.conf`, `README.md`) on the existing fence/contract/ingestion | `tools/ctrader-cli/`; `research-pipeline` routing; `_pipeline-config.md` price-primary policy; KB data-architecture + `ctrader-primary-policy` memory |
| **C3 lean pipeline** | One orchestrator with execution privilege (autonomous; stops only at critical decisions); 4 artifacts (`design.md`, `code/`, `audit.md` uncapped, `report.md`); governance inline; scope+plan merged; interpretation+report merged; registry regulated | `research-pipeline/SKILL.md` + `_pipeline-config.md`; all 4 specialist SKILLs + references |

## Verification

`scripts/verify_rollover.py --chapter 01`: Extract + Archive checks PASS; tests 17/17;
`run-experiment.sh` syntax OK; live `xen` package imports clean. The git `chapter-01-close` tag
marks the rollover commit.

## Reusable skill

This rollover was performed by the new `chapter-rollover` skill (`.claude/skills/chapter-rollover/`),
which generalizes Extract + Archive and takes the Renew change-set as a prompted-in input — reusable
at every future chapter boundary.
