# EXP-065 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-065 — MA(20,50)-Substrate Third-Barrier Geometry (Conditioned HA Harami;
`/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap; **Dual Conditioning Object: Hybrid and Native**),
Phase 015 Surface S2.
**Family / item:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-018`.
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`.
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`,
`docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`,
`docs/experiments-docs/INDEX.md` (live-status update only),
`docs/signal-registry/multiplicity-registry.md`,
`docs/signal-registry/candidate-families/harami.md`.

---

## Audit Review

| Check | Finding |
| --- | --- |
| Audit verdict | **PASS** — 0 Critical, 0 Warning, 2 Info. ✓ |
| Info 1 (DE30 truncated history) | Correctly disclosed; DE30 not among the expressing (native) viable cells — immaterial to verdict. ✓ |
| Info 2 (reconciliation FP precision) | Per-cell medians match EXP-061 to full ~17-digit FP precision; code uses tolerance-based comparison (RECON_TOL=1e-9); extra output precision is a display artifact, not a concern. ✓ |
| Critical / Warning items | None. ✓ |

## Results Review

| Check | Finding |
| --- | --- |
| Verdict consistent with data | EVIDENCE_AGAINST (native) is directly supported: 0/4 alt variants compose at P11 for the combined `median_viable ∧ beats_rm ∧ beats_bench` criterion. Max wins = 2 cells (EVENT) vs P11 quorum of 5. ✓ |
| INCONCLUSIVE (hybrid) correctly classified | Hybrid max powered cells = 4, below P11 quorum. Power limitation was predeclared in scope. Not defaulted to a ratio. ✓ |
| Native EVIDENCE_AGAINST mechanism | Interpretation correctly identifies that the same 8 core median-viable cells from EXP-061 M0 remain viable under longer horizons, but the pairwise variant−benchmark contrast CI_low > 0 never composes — longer holding does not improve median expectancy vs floor-6 cap. ✓ |
| Censoring cost bounded | Data supports this: TIMECAP fraction stays ~0.12–0.34 across all variants; event_bound_frac = 1.0 for all cells on EVENT — genuine MA-segment reversals, not backstops. ✓ |
| EXP-058 replication noted | Correct — MA-substrate result matches EXP-058 ZigZag result (no variant cleared P11); substrate convergence noted without overstatement. ✓ |
| Limitations stated | 5 predeclared limitations covered: TRAIN-only, hybrid power-limited, MA(20,50) fixed, gross returns, P15 approximation. ✓ |
| No goalpost movement | All interpretation grounded in predeclared criteria from scope.md and analysis-plan.md. No post-result criteria introduced. ✓ |

## Report Review

| Check | Finding |
| --- | --- |
| Research question and hypothesis stated | ✓ |
| Scope boundaries and exclusions | ✓ |
| Method summary with reference to analysis-plan.md | ✓ |
| Key quantitative results with sample sizes | ✓ — per-variant tables for both objects (native and hybrid), reconciliation, censoring data. |
| Audit caveats incorporated | ✓ — 2 Info notes acknowledged; neither affects verdict. |
| Conclusion uses approved result category | ✓ — EVIDENCE_AGAINST (native stronger); hybrid INCONCLUSIVE_POWER_LIMITED. |
| Links to code, results, plots, audit, governance | ✓ — full Artifacts table including post-experiment-review. |
| Follow-up recommendations as separate future experiments | ✓ — EXP-066/067/068 listed as next. |

## Index Update Review

| Artifact | Check | Finding |
| --- | --- | --- |
| `python/experiments/INDEX.md` | EXP-065 row added with correct status (EVIDENCE_AGAINST (native) / INCONCLUSIVE (hybrid)), one-line finding, and date 2026-06-18. | ✓ |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | EXP-065 added to ToC; full 5-field card appended; per-object results tables included. | ✓ |
| `docs/experiments-docs/INDEX.md` | Live status updated: Phase 015 checkpoint status advanced to note EXP-065 COMPLETE; EXP range in Family Indexes updated. | ✓ |

## Signal-Registry Disposition Review

| Check | Finding |
| --- | --- |
| Disposition recorded in report.md | ✓ — explicit `Registry Disposition` section. |
| HYP-018 outcome in multiplicity-registry.md | ✓ — status updated from PLANNED to CHARACTERISED; result recorded (native EVIDENCE_AGAINST / hybrid INCONCLUSIVE_POWER_LIMITED); 0 slots, 0 TEST reads confirmed. |
| Candidate-family status in candidate-families/harami.md | ✓ — EXP-065 result added under HYP-018 entry; family status remains REGISTERED / OPEN (no premature closure). |
| Family closure | Correctly NOT applied — P9 (no-early-closure rule) in effect; G-015 adjudicates after the full slate (EXP-066–068 remaining). ✓ |
| TEST-read ledger | No entry required — 0 TEST reads. ✓ |
| Candidate slot | Not consumed — characterisation only; registration deferred to G-015 PROCEED. ✓ |
| Refuted/inconclusive item retention | HYP-018 retained in the ledger (never deleted or renamed). ✓ |

## Core Constraint Verification

| Constraint | Finding |
| --- | --- |
| OOS holdout exclusion | Confirmed in audit — `load_train_1m` reads only F01 TRAIN prefix; longer-horizon and `/THIRD-EVENT` windows clipped to `train_end_ts` → `DATA_CENSORED`. TEST and final-30% holdout never read. ✓ |
| Causality / look-ahead safety | Confirmed in audit — MA segments bounded by crossovers before entry; `/THIRD-EVENT` exit is a forward event (next MA segment rd-confirm strictly after entry), acted on at the confirmation bar. `causality_ok = True` all 99 cells. ✓ |
| Real-price discipline | Detection on HA candles only; all metrics on real OHLC. MA(20,50) on real close. ✓ |
| Dual-object amendment compliance | Both objects reported individually; OBJECTS = ("nat","hyb"); composition_readout has separate native/hybrid blocks; no pooled statistic. Reconciliation roles corrected (native↔EXP-061 M0; hybrid↔EXP-061 H0). ✓ |
| No new countable item introduced | `/THIRD-TIME` and `/THIRD-EVENT` pre-exist from Phase 014; MA-SUBSTRATE + both conditioning modes registered at G0; no new countable item introduced. ✓ |
| Determinism | determinism_ok = True; 17/17 instrument first-usable cells replayed byte-identical. ✓ |
| Scope completeness | All 5 binding variants × 2 objects computed; 5/5 plots produced; 99/99 member cells processed; structural validation PASS. ✓ |

---

```text
VERDICT: APPROVE
```

All post-experiment checks pass: the audit is PASS with no critical or warning items; the interpretation is correctly grounded in predeclared criteria and does not move goalposts; the report is complete with quantitative evidence, audit caveats, and registry disposition; all index updates are applied correctly (no per-experiment card in the master, detailed card in the family index, live status updated); the signal-registry disposition is correctly recorded (HYP-018 measured-negative for native / power-limited for hybrid, family stays OPEN, 0 slots, 0 TEST reads, no deletion). The dual-object amendment is correctly implemented throughout. EXP-065 (Phase 015 S2) is closed; the remaining Phase 015 work is EXP-066 (S3 exits), EXP-067 (hybrid combined), and EXP-068 (native combined).
