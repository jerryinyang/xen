# Post-Experiment Governance Review: EXP-058 — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)

## Verdict: APPROVE

**Date**: 2026-06-16
**Reviewer**: Research Pipeline (automated governance)

---

## Summary

EXP-058 (HYP-011) completes the third-barrier OAT sweep on the conditioned HA harami surface. The experiment is clean — all defect gates pass, all artifacts are present and consistent, and the EVIDENCE_AGAINST verdict is mechanically justified.

---

## Constraint Compliance

### Core Constraints

| Constraint | Status | Evidence |
|-----------|--------|----------|
| Simplicity over complexity | PASS | OAT sweep of 5 predeclared variants; non-parametric regime-clustered MBB; no unnecessary computation |
| No academic-finance pitfalls | PASS | No normality, stationarity, i.i.d., or constant-volatility assumptions — all methods are non-parametric |
| Strict experiment scoping | PASS | Single hypothesis (HYP-011); defined 99-cell grid; concrete P11 success criteria; budget 4/4 methods, 5/5 plots, 1/1 module |
| Framework principles | PASS | Data-driven; non-conformational; non-parametric; real-price outcome discipline (HA detection only, real prices for all metrics); timestamp alignment |
| OOS holdout rule | PASS | Lazy scan + `slice(0, train_rows)` — full file never sorted/collected; per-cell `train_end_ts` fence; no TEST/holdout rows materialized |
| Look-ahead bias prevention | PASS | 0 causality violations; `searchsorted` + bounded forward scan; causal ZigZag; `rd`-confirm exit in future-aware only |
| Real-price discipline | PASS | HA candles used for harami detection only; all returns, excursions, and metrics on real prices (RealClose) |
| Safe performance | PASS | Per-cell bounded processing (`del cell`); lazy scans; bounded bootstrap matrices; no unbounded accumulation |

### Artifact-Specific Checks

| Artifact | Status | Notes |
|----------|--------|-------|
| `scope.md` | PASS | Hypothesis testable/falsifiable; criteria concrete; boundaries explicit; holdout excluded; real-price rule stated. Stage 4 pre-execution review confirmed. |
| `analysis-plan.md` | PASS | Method justified; assumptions listed; cross-view alignment specified; visualisation plan purposeful; interpretation guide pre-defined; budget compliant. Stage 4 confirmed. |
| `code/run_experiment.py` | PASS | All 22 code checks PASS in audit. Plan compliance, holdout exclusion, look-ahead prevention, real-price discipline, type safety, NaN handling, edge cases, separation of concerns, code quality, import side effects, progress tracking, plot memory, safe optimization all verified. |
| `audit.md` | PASS | 0 Critical, 0 Warning, 2 Info. Thoroughness confirmed (correctness, edge cases, type safety, NaN, holdout, determinism, causality, invariants). Numerical validation with spot checks and range checks. Scope compliance verified. |
| `results.md` | PASS | Honest EVIDENCE_AGAINST reporting; uncertainty acknowledged (limitations section); no overreaching; verdict mechanically justified by P11 quorum failure; next steps specific (EXP-060 combined levers). |
| `report.md` | PASS | Self-contained; key plots referenced (forest, censoring tradeoff, return distribution, contrast heatmap, r+wins composition); limitations stated; all artifacts linked by relative path. |
| `governance/pre-execution-review.md` | PASS | Verdict: APPROVE (Stage 4). No issues identified. |

---

## Index & Registry Compliance

| Check | Status | Detail |
|-------|--------|--------|
| `python/experiments/INDEX.md` | UPDATED | Row added: `EXP-058 | Third-Barrier Geometry ... | EVIDENCE_AGAINST | ... | 2026-06-16` |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | UPDATED | Full 5-field card appended with ToC entry |
| `docs/experiments-docs/INDEX.md` (master) | UPDATED | Live status includes EXP-058: `EXP-058 COMPLETE 2026-06-16 — EVIDENCE_AGAINST` |
| `docs/signal-registry/candidate-families/harami.md` | UPDATED | HYP-011/EXP-058 row status advanced from PLANNED |
| `docs/signal-registry/multiplicity-registry.md` | UPDATED | EXP-058 (`CF-HA-HARAMI-001/HYP-011`) status: `PLANNED` → `CHARACTERISED — EVIDENCE_AGAINST (2026-06-16)` |
| `docs/signal-registry/test-read-ledger.md` | UNCHANGED | 0 TEST reads consumed by EXP-058 — no update needed |
| Candidate slot accounting | CORRECT | 0 candidate slots consumed; 0 TEST reads; TRAIN-only |

---

## Verdict Rationale

**APPROVE.** All 8 core constraints pass. All artifact-specific checks pass. The audit returned 0 Critical and 0 Warning issues (2 Info: DE30 truncated-history disclosure and P15 fill-model approximation — both known, documented, and immaterial). The verdict (EVIDENCE_AGAINST) is mechanically justified: no alternative third-barrier variant clears the P11 quorum, with adequate power (99/99 cells powered on all variants). All pre-registered indexes and the signal registry have been updated. No revision is needed.
