# Governance Review: Experiment EXP-011 — Pre-Execution

**Date**: 2026-06-04
**Review Type**: Pre-Execution (consolidated; Stage 4)
**Checkpoint**: `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/loss_functions.py`

## Executive Summary

EXP-011 is the Phase 002 synthesis: under three loss functions predeclared in full, it selects a recommended per-domain operating point on the frozen EXP-006 L5 threshold τ-frontier, reports a cross-loss consistency verdict, and records a conditional adoption rule for Phase 003. It is exploratory (recommends, does not adopt). All artifacts are compliant. **VERDICT: APPROVE.**

## Phase-alignment & predeclaration check (design §2 / §4 / §8)

| Item | Finding | Verdict |
|------|---------|---------|
| Phase fit | Matches design §8 EXP-011 ("given a predeclared loss, identify the loss-minimising operating point per domain … record recommendation + conditional adoption rule") and §4 (exploratory, no pass/fail). | PASS |
| D-posture (recommend, not adopt) | Scope and code produce a *recommendation* + conditional adoption rule only; no referee/operating point is frozen. run_metadata records recommendation, not adoption. | PASS |
| D-loss predeclared "in full before any operating point is read" | All three losses **and** every coefficient (`w_*`, `c_*`, `0.50` sub cutoff, `[mat,4·mat]` band, one-grid-step tolerance, tie-breaks) are fixed in `scope.md` and as named non-tunable constants in `loss_functions.py`. The D-loss *family* was operator-confirmed 2026-06-03 (EXP-005 review token `PHASE002-PREDECLARATION-CONFIRMED`); EXP-011 is its mechanical instantiation. | PASS |
| Meta-Goodhart guardrail (§2 ⚠ / §10) | **Key risk reviewed.** The author has necessarily seen EXP-005/006/007/008 results. Mitigations verified: (a) the FP penalty term is retained in all three losses even though FPR=0 on the EXP-006 null substrate makes it inactive — it is *not* removed to favor a τ; (b) loss coefficients are neutral first-principles values (unit weights; the `0.50` cutoff is the predeclared D-lenientL5 caveat), not reverse-engineered; (c) Loss C uses a **predeclared material-edge reference prior**, deliberately not the EXP-009 empirical distribution, and the scope documents this choice as avoiding degeneracy, not as outcome-selection; (d) the recommendation is on shared draws by explicit design (D-freshdraw), with Phase 003 fresh-draw ratification as the Goodhart firewall. The scope's "Predeclaration integrity" section binds all of this and is enforceable at Stage 8. | PASS |
| Erratum citation (design §2 erratum 2026-06-03) | Scope cites the erratum and treats the lenient variant as the EXP-006 `τ=0` endpoint with a **single** τ-frontier decision space — no separate "lenient mechanism" axis (no double-counting). Analysis plan and code carry this through. | PASS |
| Single question / no scope creep | One question (loss-minimising operating point per domain + robustness). No per-instrument headline, no walk-forward re-selection, no chart-type signals, no new τ/loss — all explicitly excluded and absent from code. | PASS |

## Constraint checks

### Simplicity
| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Pure deterministic post-processing of frozen result tables. The only non-trivial step (τ>0 sub-material join) is justified and bounded; no method is more complex than the question needs. |

### Academic-finance pitfalls
| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | No normality/stationarity/iid/constant-vol assumptions. Reuses non-parametric Wilson intervals already in the frozen inputs; Loss C expectation is a finite discrete-uniform average over a predeclared grid — no parametric model. |

### Scope compliance & complexity budget
| Artifact | Verdict | Notes |
|----------|---------|-------|
| analysis-plan, code | PASS | Budget honoured: ≤2 statistical operations (precision gating + sub-material proportion estimation; loss reads are deterministic), 4/4 plots, 1/1 new module (`loss_functions.py`). No bonus analyses. |

### Principles (data-driven / non-parametric / synthetic-price / holdout)
| Artifact | Data-Driven | Non-Parametric | Synthetic-Price Discipline | Holdout Excluded |
|----------|-------------|----------------|----------------------------|------------------|
| code | PASS | PASS | PASS (no returns computed; every reused effect/MDE/TPR originates from EXP-003 real `Close` outcomes) | PASS (no market data, no `data/timebars` glob, no holdout path; reads only result-level CSV/JSON) |

### OOS holdout & look-ahead
| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout untouched | PASS | No raw bars loaded; the first-70% loader pattern appears only as the scope's mandatory safety note and is not invoked. |
| Look-ahead | PASS | No new signal construction; reused fields inherit EXP-003's `t→t+1` real returns and train-only block length. |
| Draw-key alignment | PASS | The EXP-006×EXP-003 join is on the full composite `DRAW_KEY_COLS`, never positional; many-τ-to-one fan-out on the τ-invariant `effect_bps` is asserted (zero unmatched both directions). |

### Code conventions (developer self-check verified)
| Check | Verdict | Notes |
|-------|---------|-------|
| Organization / sectioning | PASS | VAL-001 sections; imports → path → constants → I/O → pure compute → plotting → orchestration → `main()`. |
| Import side effects | PASS | Only `sys.path.insert` (house convention, mirrors EXP-009/010) + constant defs at import; dirs created in `main()`. |
| Bounded memory | PASS | Projection + scenario/α filter before `collect()` on both large draw files; aggregated to `recon` before any plot; no million-row→pandas. |
| Determinism | PASS | Pure functions; sorted byte-stable writes; no randomness. |
| Zero-baseline finite | PASS | `sub_rate` `otherwise(0.0)` with explicit pass-count; `1−TPR` bounded. |
| Magic numbers | PASS | All knobs named, annotated predeclared; `MATERIALITY_BPS` asserted against `xen.referee_calibration`; `G_d` asserted inside `[mat,4·mat]`. |
| Hard gates | PASS | Dependency-token, precision (D-prec), and EXP-007 τ=0 reproduction gates raise/flag — never silently pass. |
| Progress / logging | PASS | Concise `logging`; no tqdm needed (3×7 trivial loops; join is one vectorised op) — justified. |
| Safe optimization | PASS | Polars group-by preserves denominators/keys; lexicographic selection kept explicit over 21 rows; no change to sample membership, ordering, denominators, or interpretation. |

## Dependency-maturity note (recorded, non-blocking for pre-execution)

EXP-008 (hard dependency) and EXP-009/010 (context) have produced results and passed pre-execution review + adversarial code review, but have **not** completed their own Stage 5–8 (no `audit.md`/`results.md`/`report.md`/post-experiment review; not yet in INDEX). A lightweight correctness check of all three was performed 2026-06-04 (EXP-008 H-pool arithmetic and FPR verified; EXP-009 distribution-summary reconciled with per-cell table; EXP-010 single-split reproduction + walk-forward verdicts verified) and found them sound. Pre-execution design may proceed against these frozen artifacts. **Execution gate:** EXP-011 should be *run* only after EXP-008 (and ideally EXP-009/010) complete post-experiment governance, so the synthesis cites validated dependencies. This is an operator sequencing decision, recorded here, not a governance block on the pre-execution artifacts.

## Findings

### Critical
None.

### Warnings
None.

### Info
1. On the EXP-006 null substrate FPR=0 at every τ, so the FPR term and Loss A's hard FPR constraint will not bind; the sub-material term is expected to be the economically binding criterion (scope anticipates this; the FP term is retained by predeclaration, not pruned).
2. The τ>0 sub-material reconstruction depends on the EXP-006×EXP-003 draw-key alignment that EXP-007 already relied on; the mandatory τ=0 reproduction gate against EXP-007 will catch any reconstruction drift at run time.

## Verdict

```text
VERDICT: APPROVE
```
