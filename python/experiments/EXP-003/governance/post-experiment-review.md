# Post-Experiment Governance Review: EXP-003 (Keystone)

**Stage**: 8 (post-experiment)
**Artifacts reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`

---

## Constraint Checks

| Constraint | Result | Evidence |
|------------|--------|----------|
| Single hypothesis / strict scoping | PASS | One operating-characteristic-measurement hypothesis; budget 4/4 tests, 5/5 plots, shared module reused (no new module). |
| OOS holdout untouched | PASS | First-70% slice; domain row counts reproduce EXP-001 post-slice (BTC 4h=4425); end-to-end reproduction confirms no holdout access. |
| Chronological / shared split | PASS | `domain_split_index` applies the shared `train_end_ts` to each domain (BTC 4h split=3089 reproduced), not per-domain row fractions (design §9). |
| Look-ahead prevention | PASS | States independent of returns; outcome `t→t+1`; block length on train segment only. |
| Real-price discipline | PASS | Real domain `Close` returns; no chart-type/synthetic prices. |
| Determinism / safe optimization | PASS | Multiprocessing is scheduling-only; per-draw seed regeneration + canonical sort; reproduced bit-for-bit against `draw_verdicts.csv`. |
| Paired-draw design | PASS | Identical draws to both referees via shared seed (audit reproduction). |
| No academic-finance pitfalls | PASS | Distribution-free Wilson intervals; block-bootstrap serial-dependence-aware inference; effective-N reported. |
| Measured stringency deliverable | PASS | Per-domain FPR/TPR/MDE/per-leg map produced with usable precision (18/18 cells). |
| No referee redesign / meta-Goodhart | PASS | Frozen referees measured once; no post-hoc rule changes; results.md proposes only new scopes. |
| Audit thoroughness & evidence | PASS | End-to-end reproduction, Wilson/MDE arithmetic, per-leg diagnostics; 0 Critical, 0 Warning, 3 Info. |
| Results honesty & verdict support | PASS | SUPPORTED tied to Evidence-FOR; pooling and blind-vs-not-blind caveats stated; next steps are new scopes. |
| Report self-contained & linked | PASS | Trade-off table + 3 key plots; artifacts linked. |
| Indexes updated | PASS | Brief and comprehensive indexes both updated. |
| Phase alignment | PASS | Matches design §4 H-keystone (measures) and §10 EXP-003; hands the MDE map to EXP-004 for anchoring. |

## Findings

No Critical or Warning issues. The audit's three Info notes — instrument pooling
within a domain (consistent with the per-domain deliverable), MDE-as-first-grid-
crossing under TPR monotonicity, and the α-invariant materiality-driven gate
operating point — are correctly characterized. The pooling note is carried into
EXP-004, which evaluates per-instrument dogfood against these per-domain MDEs.

The keystone's primary measured result (gate-stack stringency trades FPR→0 for a
2–8× larger MDE, with L5 the binding leg) is the design's intended deliverable
(§11: "success is stating the operating characteristics"), and it is reported as a
measurement, not as a gate-stack endorsement — satisfying the meta-Goodhart
guardrail.

## Verdict

```text
VERDICT: APPROVE
```

EXP-003 is complete and the operating-characteristic map exists with usable
precision on all three domains. EXP-004 may proceed to anchor the map against the
real Donchian / MA dogfood strategies.
