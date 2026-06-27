# Post-Experiment Governance Review — EXP-076 (`ASS`/VAL-001)

**Reviewed:** `audit.md`, `results.md`, `report.md`, and the index/registry updates against the bundled
governance constraints + the Phase 017 D0. **Date:** 2026-06-20. **Stage:** 8 (post-experiment).

## Constraint checks

| Constraint | Result |
| --- | --- |
| OOS holdout untouched | **PASS** — synthetic only; no Parquet load, no slice, no holdout path. |
| Look-ahead / temporal causality | **PASS (N/A)** — synthetic iid; determinism via fixed `SeedSequence` (D6). |
| Real-price discipline | **PASS (N/A)** — synthetic ATR-unit returns; no HA/Renko prices. |
| Single hypothesis / scope boundaries | **PASS** — one question (recovery of known truth); no scope creep. |
| Complexity budget | **PASS** — 3 checks / 4 plots / 1 module (`xen.ass`), as scoped. |
| Gate-threshold calibration | **PASS** — 0.85·SE, [0.86,0.94], 0.25/0.05 are fixture/bite-calibrated, not magic. |
| **Verdict representation (per-stratum)** | **PASS (post-fix)** — `verdict.json` is per-stratum (recovery / coverage-by-n / shrinkage); `overall_pass_literal` removed; the only collapsed field is `collapsed_convenience_flag`, explicitly non-binding. The original collapsed verdict was the audit's C1 and is resolved. |
| Audit verdict forensics present | **PASS** — autonomous per-stratum re-derivation, explicit mechanism, gate-shape check all present. |
| Audit per-stratum masking check | **PASS** — audit affirmatively showed the pooled FAIL masked heterogeneity (4/198 cells, all n=15 expectancy + the n=2000 predeclared marginal); independently re-derived. |
| Audit materiality & blocking | **PASS** — C1 classed Critical (representation-material), routed to developer, fixed, re-audited; the coverage miss correctly classed as the genuine measured outcome (sense ii), not a bug; no verdict-bearing number moved by code defect. |
| Interpretation honesty / no overreach | **PASS** — `results.md` reports per-stratum, states the n=15 caveat plainly, does not inflate; follow-ups are new scopes (EXP-077/078). |
| Report self-contained / artifacts linked | **PASS** — `report.md` carries the per-stratum result, C1 history, dispositions, plots, relative-path links. |
| Indexes updated | **PASS** — `python/experiments/INDEX.md` row; family detail card in `families/cf-capgeo-001/INDEX.md`; master live status + Family Indexes table only. |
| Registry & ledger disposition | **PASS** — multiplicity-registry item outcome set (retained); candidate-family gate row advanced; global-techniques `ASS` note; **0 counted TEST reads**, ledger unchanged (recorded in `report.md`). |

## Verdict-forensics confirmation (Stage-8 requirement)

The audit carried the full forensics autonomously: a per-stratum re-derivation with an explicit masking
check (pooled `overall_pass_literal=false` shown to be 194/198-passing, driven only by the n=15
expectancy floor + the predeclared n=2000 marginal), a mechanism statement (intrinsic small-sample
percentile-bootstrap under-coverage of the mean, expectancy-specific, shape-ordered, independently
reproduced), and a gate-shape check (the uniform all-cells conjunction over-aggregates the n=15
sparse-stress regime). The one verdict-material finding (C1) was **fixed and re-audited**, not
down-classified — representation-only, so no recompute of binding numbers was required, and the table
hashes are byte-identical across the regeneration.

## Disposition

Two items are **carried to the operator / G-017 as governance decisions** (not blocking this review):
(a) ratify coverage binding at **n≥30** with n=15 expectancy as a disclosed sparse-stress diagnostic
via a dated `D0-amendment`; (b) the downstream propagation guard (no expectancy edge-calls at effective
n<30; EXP-077 small-n FPR stratum) plus the n=2000 rich-pull reading. These are correctly framed as
G-017 inputs; EXP-076 does not prejudge them in code.

Anti-reversion guard for the C1 failure mode is in place: a per-stratum verdict check + REVISE trigger
in `governance-constraints.md` (Stage 4/8, every experiment) and `LESSON-001-per-stratum-verdict.md`.

```text
VERDICT: APPROVE
```
